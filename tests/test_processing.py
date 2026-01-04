import importlib.util

import pytest

cv2_spec = importlib.util.find_spec("cv2")
numpy_spec = importlib.util.find_spec("numpy")
pillow_spec = importlib.util.find_spec("PIL")
pdf2image_spec = importlib.util.find_spec("pdf2image")

if not (cv2_spec and numpy_spec and pillow_spec and pdf2image_spec):  # pragma: no cover - environment dependent
    pytest.skip("Skipping processing tests; dependencies not available", allow_module_level=True)

import cv2  # type: ignore  # noqa: E402
import numpy as np  # type: ignore  # noqa: E402

from processing import deskew_opencv  # noqa: E402


def _rotated_rect_image(angle: float) -> np.ndarray:
    img = np.full((200, 200), 255, dtype=np.uint8)
    rect = ((100, 100), (120, 40), angle)
    box = cv2.boxPoints(rect).astype(np.int32)
    cv2.fillPoly(img, [box], 0)
    return img


def test_deskew_skips_unreasonable_angles():
    # When the detected angle is high (likely a false positive), deskew should
    # leave the image unchanged to avoid introducing rotations.
    arr = _rotated_rect_image(60)
    result = deskew_opencv(arr, sensitivity=0.5)
    assert np.array_equal(result, arr)
