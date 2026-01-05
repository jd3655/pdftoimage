from pathlib import Path
import importlib.util
import sys

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "utils.py"
spec = importlib.util.spec_from_file_location("pdftoimage_utils", MODULE_PATH)
utils = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
assert spec and spec.loader
spec.loader.exec_module(utils)  # type: ignore[arg-type]
sys.modules["pdftoimage_utils"] = utils
filter_supported = utils.filter_supported
pdf_page_filename = utils.pdf_page_filename
safe_stem = utils.safe_stem
temporary_named_file = utils.temporary_named_file
unique_name = utils.unique_name


def test_unique_name_collision():
    existing = {"receipt.png", "receipt-1.png"}
    assert unique_name(existing, "receipt.png") == "receipt-2.png"
    assert unique_name(existing, "newfile.png") == "newfile.png"


def test_pdf_page_filename_format():
    assert pdf_page_filename("report", 1) == "report_page_001.png"
    assert pdf_page_filename("report", 12) == "report_page_012.png"


def test_filter_supported_ignores_hidden_and_system(tmp_path: Path):
    hidden = tmp_path / ".DS_Store"
    hidden.write_text("ignore")
    system = tmp_path / "__MACOSX" / "file.pdf"
    system.parent.mkdir()
    system.write_text("ignore")
    good = tmp_path / "invoice.pdf"
    good.write_text("content")

    result = filter_supported([hidden, system, good])
    assert result == [good]


def test_safe_stem_sanitizes():
    assert safe_stem("inv*oice 01.pdf") == "invoice_01"
    assert safe_stem("   .pdf") == "file"


def test_temporary_named_file_uses_stem(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(utils.tempfile, "gettempdir", lambda: tmp_path)
    out_path = temporary_named_file("receipt-123456.pdf", ".zip")
    assert out_path.name == "receipt-123456.zip"
    assert out_path.parent == tmp_path


def test_temporary_named_file_increments_when_taken(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(utils.tempfile, "gettempdir", lambda: tmp_path)
    existing = tmp_path / "receipt-123456.zip"
    existing.touch()
    out_path = temporary_named_file("receipt-123456", ".zip")
    assert out_path.name == "receipt-123456-1.zip"
