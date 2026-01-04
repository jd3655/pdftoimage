import importlib
import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageOps

_heif_spec = importlib.util.find_spec("pillow_heif")
if _heif_spec:
    pillow_heif = importlib.import_module("pillow_heif")
    pillow_heif.register_heif_opener()  # type: ignore
else:
    pillow_heif = None  # Optional; continue without HEIC support

_cv2_spec = importlib.util.find_spec("cv2")
if not _cv2_spec:  # pragma: no cover - guarded by requirements
    raise RuntimeError("OpenCV is required for image processing")
cv2 = importlib.import_module("cv2")

_pdf_spec = importlib.util.find_spec("pdf2image")
if not _pdf_spec:  # pragma: no cover - guarded by requirements
    raise RuntimeError("pdf2image is required for PDF rendering")
convert_from_path = importlib.import_module("pdf2image").convert_from_path

from utils import (
    ensure_unique_path,
    filter_supported,
    is_supported_file,
    pdf_page_filename,
    safe_stem,
    unique_name,
    zip_directory_to_file,
)


MAX_PDF_PAGES = 200
MAX_TOTAL_FILES = 500


@dataclass
class Settings:
    dpi: int = 400
    grayscale: bool = True
    auto_orient: bool = True
    deskew: bool = True
    deskew_sensitivity: float = 0.4
    contrast_stretch: bool = True
    contrast_percent: float = 0.5
    trim: bool = True
    adaptive_threshold: bool = False
    mode: str = "Balanced"


class CancellationFlag:
    def __init__(self) -> None:
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def check(self) -> bool:
        return self.cancelled


def process_inputs(
    files: List[str] | None,
    zip_path: Optional[str],
    settings: Settings,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_flag: Optional[CancellationFlag] = None,
) -> Tuple[Path, str]:
    all_inputs: List[Path] = []
    if files:
        all_inputs.extend(filter_supported(files))

    if zip_path:
        from utils import collect_files_from_zip  # Local import to avoid cycles

        extracted = collect_files_from_zip(zip_path)
        all_inputs.extend(extracted)

    if len(all_inputs) == 0:
        raise ValueError("No supported files found.")

    if len(all_inputs) > MAX_TOTAL_FILES:
        raise ValueError(f"Too many files. Limit is {MAX_TOTAL_FILES}.")

    temp_dir = Path(tempfile.mkdtemp(prefix="pdftoimage_out_"))
    receipts_dir = temp_dir / "receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)

    existing_paths = set()
    log_lines: List[str] = []
    manifest: List[Dict[str, object]] = []

    total = len(all_inputs)
    for idx, input_path in enumerate(all_inputs, start=1):
        if cancel_flag and cancel_flag.check():
            log_lines.append("Processing cancelled by user.")
            break
        rel_progress = (idx - 1) / total
        _maybe_progress(progress_cb, rel_progress, f"Processing {input_path.name}")
        if input_path.suffix.lower() == ".pdf":
            try:
                outputs = process_pdf(input_path, temp_dir, settings, existing_paths, progress_cb, cancel_flag)
                manifest.append({"input": str(input_path), "outputs": [str(p) for p in outputs]})
                log_lines.append(f"Processed PDF {input_path.name} -> {len(outputs)} pages")
            except Exception as exc:  # pragma: no cover - runtime errors
                log_lines.append(f"Failed PDF {input_path.name}: {exc}")
        else:
            try:
                output_path = process_image(input_path, receipts_dir, settings, existing_paths)
                manifest.append({"input": str(input_path), "outputs": [str(output_path)]})
                log_lines.append(f"Processed image {input_path.name} -> {output_path.name}")
            except Exception as exc:  # pragma: no cover - runtime errors
                log_lines.append(f"Failed image {input_path.name}: {exc}")

    _write_metadata(temp_dir, log_lines, manifest)

    zip_out = Path(tempfile.mkstemp(prefix="result_", suffix=".zip")[1])
    zip_directory_to_file(temp_dir, zip_out)
    _maybe_progress(progress_cb, 1.0, "Packaging complete")
    return zip_out, "\n".join(log_lines)


def process_pdf(
    pdf_path: Path,
    output_root: Path,
    settings: Settings,
    existing_paths: set,
    progress_cb: Optional[Callable[[float, str], None]] = None,
    cancel_flag: Optional[CancellationFlag] = None,
) -> List[Path]:
    stem = safe_stem(pdf_path.name)
    pdf_folder_name = unique_name({p.parts[0] for p in existing_paths if len(p.parts) > 1}, stem)
    pdf_dir = output_root / pdf_folder_name
    pdf_dir.mkdir(exist_ok=True)

    try:
        pages = convert_from_path(
            pdf_path,
            dpi=settings.dpi,
            fmt="png",
            first_page=1,
            last_page=MAX_PDF_PAGES,
        )
    except Exception as exc:
        raise RuntimeError(
            "Failed to render PDF. Ensure Poppler is installed and on your PATH."
        ) from exc

    outputs: List[Path] = []
    total_pages = len(pages)
    for i, page in enumerate(pages, start=1):
        if cancel_flag and cancel_flag.check():
            break
        _maybe_progress(progress_cb, i / max(total_pages, 1), f"Rendering page {i}/{total_pages}")
        processed = preprocess_pil_image(page, settings)
        file_name = pdf_page_filename(pdf_folder_name, i)
        unique_file = ensure_unique_path(Path(pdf_folder_name), file_name, existing_paths)
        output_path = output_root / pdf_folder_name / unique_file
        processed.save(output_path, format="PNG", optimize=True)
        outputs.append(output_path)
    return outputs


def process_image(
    image_path: Path,
    output_dir: Path,
    settings: Settings,
    existing_paths: set,
) -> Path:
    img = Image.open(image_path)
    processed = preprocess_pil_image(img, settings)
    base_name = safe_stem(image_path.name) + ".png"
    unique_file = ensure_unique_path(Path("receipts"), base_name, existing_paths)
    output_path = output_dir / unique_file
    processed.save(output_path, format="PNG", optimize=True)
    return output_path


def preprocess_pil_image(img: Image.Image, settings: Settings) -> Image.Image:
    if settings.auto_orient:
        img = ImageOps.exif_transpose(img)

    if settings.grayscale:
        img = img.convert("L")
    else:
        img = img.convert("RGB")

    arr = np.array(img)

    if settings.contrast_stretch:
        arr = contrast_stretch_numpy(arr, settings.contrast_percent)

    if settings.mode.lower().startswith("aggressive"):
        h = 7
    else:
        h = 5
    if len(arr.shape) == 2:
        denoised = cv2.fastNlMeansDenoising(arr, h=h)
    else:
        denoised = cv2.fastNlMeansDenoisingColored(arr, h=h, hColor=h)
    arr = denoised

    if settings.deskew:
        arr = deskew_opencv(arr, settings.deskew_sensitivity)

    if settings.trim:
        arr = trim_whitespace(arr)

    if settings.adaptive_threshold and len(arr.shape) == 2:
        arr = cv2.adaptiveThreshold(
            arr,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15,
        )

    mode = "L" if settings.grayscale else "RGB"
    return Image.fromarray(arr).convert(mode)


def contrast_stretch_numpy(arr: np.ndarray, percent: float) -> np.ndarray:
    percent = max(0.2, min(percent, 2.0))
    low = percent
    high = 100 - percent
    if arr.ndim == 2:
        lo, hi = np.percentile(arr, (low, high))
        stretched = np.clip((arr - lo) * 255.0 / max(hi - lo, 1e-3), 0, 255)
        return stretched.astype(np.uint8)
    else:
        out = np.empty_like(arr)
        for c in range(arr.shape[2]):
            lo, hi = np.percentile(arr[:, :, c], (low, high))
            out[:, :, c] = np.clip((arr[:, :, c] - lo) * 255.0 / max(hi - lo, 1e-3), 0, 255)
        return out.astype(np.uint8)


def deskew_opencv(arr: np.ndarray, sensitivity: float) -> np.ndarray:
    gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(thresh < 255))
    if coords.size == 0:
        return arr
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if math.isclose(angle, 0, abs_tol=0.1):
        return arr
    # Documents rarely need more than a small correction; large angles often
    # indicate that the detected contour is not representative of the page
    # (e.g. a diagonal element near the edge). Skip adjustment when the
    # detected angle is beyond a reasonable threshold to avoid rotating pages
    # incorrectly, while still allowing small de-skews.
    if abs(angle) > 15:
        return arr
    angle *= max(0.1, min(sensitivity, 1.0))
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(arr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def trim_whitespace(arr: np.ndarray, threshold: int = 250) -> np.ndarray:
    gray = arr if arr.ndim == 2 else cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    coords = cv2.findNonZero(255 - gray)
    if coords is None:
        return arr
    x, y, w, h = cv2.boundingRect(coords)
    return arr[y : y + h, x : x + w]


def _write_metadata(temp_dir: Path, log_lines: List[str], manifest: List[Dict[str, object]]) -> None:
    (temp_dir / "processing_log.txt").write_text("\n".join(log_lines), encoding="utf-8")
    (temp_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _maybe_progress(cb: Optional[Callable[[float, str], None]], fraction: float, desc: str) -> None:
    if cb:
        cb(fraction, desc)
