from pathlib import Path

import pytest

from utils import filter_supported, pdf_page_filename, safe_stem, unique_name


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
