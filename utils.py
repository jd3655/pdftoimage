import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, List, Set

SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic"}


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
    extracted_files: List[Path] = []
    target_dir = Path(tempfile.mkdtemp(prefix="pdftoimage_zip_"))
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = Path(member.filename)
            if member.is_dir():
                continue
            if is_hidden_path(member_path):
                continue
            dest_path = target_dir / member.filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            if is_supported_file(dest_path):
                extracted_files.append(dest_path)
    return extracted_files


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
