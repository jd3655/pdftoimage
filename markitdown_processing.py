import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from markitdown import MarkItDown

from processing import MAX_TOTAL_FILES
from utils import (
    ensure_unique_path,
    is_hidden_path,
    safe_extract_with_relative,
    safe_stem,
    temporary_named_file,
    zip_directory_to_file,
)


@dataclass
class MarkItDownOptions:
    enable_plugins: bool = False
    use_docintel: bool = False
    docintel_endpoint: Optional[str] = None
    docintel_key: Optional[str] = None
    use_llm_descriptions: bool = False
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_prompt: Optional[str] = None
    llm_api_key: Optional[str] = None
    output_format: str = "Markdown + manifest JSON"
    youtube_url: Optional[str] = None


class MarkItDownError(Exception):
    """Wrapper for MarkItDown-specific errors."""


def _load_markitdown():
    try:
        from markitdown import MarkItDown  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise MarkItDownError(
            "MarkItDown is required for this backend. Install markitdown[all] to continue."
        ) from exc
    return MarkItDown


def _build_llm_client(options: MarkItDownOptions):
    if not options.use_llm_descriptions:
        return None
    if not options.llm_provider:
        return None
    provider = options.llm_provider.lower()
    api_key = options.llm_api_key or os.getenv("OPENAI_API_KEY")
    if provider == "openai":
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise MarkItDownError(f"OpenAI client unavailable: {exc}") from exc
        if not api_key:
            raise MarkItDownError("OpenAI API key is required for LLM image descriptions.")
        return OpenAI(api_key=api_key)
    raise MarkItDownError(f"Unsupported LLM provider: {options.llm_provider}")


def _create_markitdown_instance(options: MarkItDownOptions):
    MarkItDown = _load_markitdown()
    kwargs: Dict[str, Any] = {"enable_plugins": options.enable_plugins}
    if options.use_docintel and options.docintel_endpoint:
        kwargs["docintel_endpoint"] = options.docintel_endpoint
        if options.docintel_key:
            os.environ.setdefault("AZURE_DOCUMENT_INTELLIGENCE_KEY", options.docintel_key)
    if options.use_llm_descriptions:
        client = _build_llm_client(options)
        if client:
            kwargs["llm_client"] = client
        if options.llm_model:
            kwargs["llm_model"] = options.llm_model
        if options.llm_prompt:
            kwargs["llm_prompt"] = options.llm_prompt
    try:
        return MarkItDown(**kwargs)
    except TypeError as exc:
        # Older MarkItDown versions do not support `enable_plugins`. Retry without it.
        if "enable_plugins" in kwargs and "enable_plugins" in str(exc):
            retry_kwargs = dict(kwargs)
            retry_kwargs.pop("enable_plugins", None)
            try:
                return MarkItDown(**retry_kwargs)
            except Exception as retry_exc:
                raise MarkItDownError(
                    "Failed to initialize MarkItDown after removing the enable_plugins option. "
                    "Please upgrade markitdown to a version that supports plugins."
                ) from retry_exc
        raise MarkItDownError(f"Failed to initialize MarkItDown: {exc}") from exc


def _markdown_from_result(result: Any) -> Tuple[str, Dict[str, Any]]:
    markdown_text = (
        getattr(result, "text_content", None)
        or getattr(result, "markdown", None)
        or getattr(result, "content", None)
    )
    if markdown_text is None:
        markdown_text = str(result)
    metadata = getattr(result, "metadata", None) or {}
    return markdown_text, _normalize_metadata(metadata)


def _normalize_metadata(metadata: Any) -> Any:
    try:
        json.dumps(metadata)
        return metadata
    except TypeError:
        return str(metadata)


def convert_item_to_markdown(
    converter,
    source: str | Path,
    relative_path: Path,
    output_dir: Path,
    existing_paths: set,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    """Convert a single item with MarkItDown. Returns output path and manifest entry."""
    source_str = str(source)
    manifest_entry: Dict[str, Any] = {
        "input": source_str,
        "relative_path": relative_path.as_posix(),
        "backend": "markitdown",
    }
    try:
        try:
            result = converter.convert(source_str)
        except TypeError:
            # Older versions may require a stream; fall back.
            with open(source, "rb") as f:
                result = converter.convert_stream(f, file_name=relative_path.name)
        markdown_text, metadata = _markdown_from_result(result)
        rel_dir = relative_path.parent
        base_name = safe_stem(relative_path.name) + ".md"
        unique_file = ensure_unique_path(rel_dir, base_name, existing_paths)
        output_path = output_dir / rel_dir / unique_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_text, encoding="utf-8")
        manifest_entry.update(
            {
                "status": "success",
                "output": output_path.relative_to(output_dir).as_posix(),
                "metadata": metadata,
            }
        )
        return output_path, manifest_entry
    except Exception as exc:
        manifest_entry.update({"status": "failed", "error": str(exc)})
        return None, manifest_entry


def _gather_inputs(
    files: List[str] | None,
    zip_path: Optional[str],
    youtube_url: Optional[str],
    max_files: int,
) -> List[Tuple[str | Path, Path]]:
    gathered: List[Tuple[str | Path, Path]] = []
    if files:
        for f in files:
            path = Path(f)
            if is_hidden_path(path):
                continue
            gathered.append((path, Path(path.name)))
    if zip_path:
        remaining = max_files - len(gathered)
        if remaining <= 0:
            raise ValueError(f"Too many files. Limit is {max_files}.")
        extracted, _ = safe_extract_with_relative(zip_path, max_entries=remaining)
        for path, rel in extracted:
            gathered.append((path, rel))
    if youtube_url and youtube_url.strip():
        gathered.append((youtube_url.strip(), Path("youtube_source.md")))
    if len(gathered) == 0:
        raise ValueError("No supported files found.")
    if len(gathered) > max_files:
        raise ValueError(f"Too many files. Limit is {max_files}.")
    return gathered


def convert_batch_to_outputs(
    files: List[str] | None,
    zip_path: Optional[str],
    options: MarkItDownOptions,
    progress_cb=None,
) -> Tuple[Path, Dict[str, Any], str]:
    """Process inputs with MarkItDown and package outputs."""
    gathered = _gather_inputs(files, zip_path, options.youtube_url, MAX_TOTAL_FILES)
    output_root = Path(tempfile.mkdtemp(prefix="markitdown_out_"))
    converter = _create_markitdown_instance(options)

    manifest: List[Dict[str, Any]] = []
    log_lines: List[str] = []
    aggregate_outputs: List[Dict[str, Any]] = []
    existing_paths: set = set()

    total = len(gathered)
    for idx, (source, rel_path) in enumerate(gathered, start=1):
        if progress_cb:
            progress_cb((idx - 1) / total, f"Converting {rel_path.name}")
        output_path, entry = convert_item_to_markdown(converter, source, rel_path, output_root, existing_paths)
        manifest.append(entry)
        if entry.get("status") == "success" and output_path:
            aggregate_outputs.append(
                {
                    "input": entry["input"],
                    "markdown_path": entry["output"],
                    "metadata": entry.get("metadata") or {},
                }
            )
            log_lines.append(f"Converted {rel_path} -> {output_path.relative_to(output_root)}")
        else:
            log_lines.append(f"Failed {rel_path}: {entry.get('error')}")
    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log_text = "\n".join(log_lines)
    (output_root / "processing.log").write_text(log_text, encoding="utf-8")
    (output_root / "processing_log.txt").write_text(log_text, encoding="utf-8")

    if options.output_format.lower().startswith("markdown + manifest"):
        (output_root / "markdown_manifest.json").write_text(
            json.dumps(aggregate_outputs, indent=2),
            encoding="utf-8",
        )
    primary_input = gathered[0][0] if gathered else None
    if isinstance(primary_input, Path):
        zip_out = temporary_named_file(primary_input.name, ".zip")
    else:
        zip_out = temporary_named_file("result", ".zip")
    zip_directory_to_file(output_root, zip_out)
    if progress_cb:
        progress_cb(1.0, "Packaging complete")
    return zip_out, {"manifest": manifest, "log": log_text}, log_text
