from __future__ import annotations

import fitz
import pytest

from ocr_pipeline.limits import (
    InputTooLarge,
    check_dpi,
    check_pdf_pages,
    check_upload_size,
    count_pdf_pages,
)


def _make_pdf(path, pages: int) -> None:
    doc = fitz.open()
    for n in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"page {n + 1}")
    doc.save(str(path))
    doc.close()


class TestUploadSize:
    def test_accepts_within_limit(self):
        check_upload_size(1024, 2048)

    def test_rejects_over_limit(self):
        with pytest.raises(InputTooLarge, match="limit is"):
            check_upload_size(4096, 2048)

    def test_rejects_empty(self):
        with pytest.raises(InputTooLarge, match="empty"):
            check_upload_size(0, 2048)

    def test_boundary_is_inclusive(self):
        check_upload_size(2048, 2048)


class TestDpi:
    def test_accepts_default(self):
        check_dpi(300, 400)

    def test_rejects_too_high(self):
        with pytest.raises(InputTooLarge, match="exceeds the maximum"):
            check_dpi(1200, 400)

    def test_rejects_too_low(self):
        with pytest.raises(InputTooLarge, match="at least 72"):
            check_dpi(10, 400)


class TestPdfPages:
    def test_counts_pages(self, tmp_path):
        pdf = tmp_path / "three.pdf"
        _make_pdf(pdf, 3)
        assert count_pdf_pages(pdf) == 3

    def test_accepts_within_limit(self, tmp_path):
        pdf = tmp_path / "small.pdf"
        _make_pdf(pdf, 3)
        assert check_pdf_pages(pdf, max_pages=10) == 3

    def test_rejects_page_heavy_pdf(self, tmp_path):
        # The scenario that matters: small file, many pages.
        pdf = tmp_path / "many.pdf"
        _make_pdf(pdf, 40)
        assert pdf.stat().st_size < 1024 * 1024  # tiny on disk
        with pytest.raises(InputTooLarge, match="40 pages; limit is 10"):
            check_pdf_pages(pdf, max_pages=10)

    def test_rejects_corrupt_pdf(self, tmp_path):
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"this is not a pdf")
        with pytest.raises(InputTooLarge, match="could not read PDF"):
            check_pdf_pages(bad, max_pages=10)
