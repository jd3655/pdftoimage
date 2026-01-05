import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Iterable, List, Set

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic"}
# Broader set used for MarkItDown-driven processing; MarkItDown will route
# internally and may support more types, but these are safe for UI hints.
MARKITDOWN_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".tif",
    ".tiff",
    ".heic",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".json",
    ".xml",
    ".html",
    ".htm",
    ".epub",
    ".mp3",
    ".wav",
    ".zip",
}


def is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") or part == "__MACOSX" for part in path.parts)


def is_supported_file(path: str | Path) -> bool:
    p = Path(path)
    if is_hidden_path(p):
        return False
    return p.suffix.lower() in SUPPORTED_EXTENSIONS


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = stem.strip().replace(" ", "_")
    stem = re.sub(r"[^A-Za-z0-9_-]", "", stem)
    return stem or "file"


def unique_name(existing: Set[str], desired: str) -> str:
    if desired not in existing:
        return desired
    path = Path(desired)
    stem = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = f"{stem}-{counter}{suffix}"
        if candidate not in existing:
            return candidate
        counter += 1


def pdf_page_filename(stem: str, page_index: int) -> str:
    return f"{stem}_page_{page_index:03d}.png"


def zip_directory_to_file(dir_path: Path, out_zip_path: Path) -> Path:
    with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(dir_path)
                zf.write(full_path, rel_path.as_posix())
    return out_zip_path


def collect_files_from_zip(zip_path: str | Path) -> List[Path]:
    return collect_files_from_zip_generic(zip_path, filter_fn=is_supported_file)


def ensure_unique_path(rel_dir: Path, filename: str, existing_paths: Set[Path]) -> Path:
    base_stem = Path(filename).stem
    suffix = Path(filename).suffix
    candidate = Path(filename)
    counter = 1
    while (rel_dir / candidate) in existing_paths:
        candidate = Path(f"{base_stem}-{counter}{suffix}")
        counter += 1
    existing_paths.add(rel_dir / candidate)
    return candidate


def filter_supported(paths: Iterable[str | Path]) -> List[Path]:
    return [Path(p) for p in paths if is_supported_file(p)]


def collect_files_from_zip_generic(
    zip_path: str | Path,
    filter_fn: Callable[[Path], bool] | None = None,
    max_entries: int | None = None,
) -> List[Path]:
    extracted_files: List[Path] = []
    extracted, _ = safe_extract_with_relative(zip_path, filter_fn, max_entries)
    for path, _ in extracted:
        extracted_files.append(path)
    return extracted_files


def safe_extract_with_relative(
    zip_path: str | Path,
    filter_fn: Callable[[Path], bool] | None = None,
    max_entries: int | None = None,
) -> tuple[List[tuple[Path, Path]], Path]:
    extracted: List[tuple[Path, Path]] = []
    target_dir = Path(tempfile.mkdtemp(prefix="pdftoimage_zip_"))
    base_dir = target_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = Path(member.filename)
            if member.is_dir():
                continue
            if is_hidden_path(member_path):
                continue
            dest_path = target_dir / member.filename
            resolved = dest_path.resolve()
            if not str(resolved).startswith(str(base_dir)):
                # Zip-slip attempt; skip entry
                continue
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            if filter_fn is None or filter_fn(dest_path):
                extracted.append((dest_path, member_path))
            if max_entries and len(extracted) >= max_entries:
                break
    return extracted, target_dir


def temporary_named_file(stem: str, suffix: str) -> Path:
    base = safe_stem(stem)
    temp_dir = Path(tempfile.gettempdir())
    candidate = temp_dir / f"{base}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = temp_dir / f"{base}-{counter}{suffix}"
        counter += 1
    return candidate
