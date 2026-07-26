"""Input validation shared by the FastAPI app and the RunPod handler.

These are the guards that make the service safe to expose. Page count matters
more than byte count: a 2 MB, 200-page PDF becomes 200 full-resolution PNGs fed
to the model in a single infer_multi call.
"""

from __future__ import annotations

from pathlib import Path

import fitz


class InputTooLarge(ValueError):
    """Raised when an upload exceeds a configured limit."""


def check_upload_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes <= 0:
        raise InputTooLarge("uploaded file is empty")
    if size_bytes > max_bytes:
        raise InputTooLarge(
            f"file is {size_bytes} bytes; limit is {max_bytes} bytes "
            f"({max_bytes // (1024 * 1024)} MB)"
        )


def check_dpi(dpi: int, max_dpi: int) -> None:
    if dpi < 72:
        raise InputTooLarge("dpi must be at least 72")
    if dpi > max_dpi:
        raise InputTooLarge(f"dpi {dpi} exceeds the maximum of {max_dpi}")


def count_pdf_pages(pdf_path: str | Path) -> int:
    """Page count without rendering anything."""
    try:
        document = fitz.open(str(pdf_path))
    except Exception as exc:  # corrupt or not actually a PDF
        raise InputTooLarge(f"could not read PDF: {exc}") from exc
    try:
        return document.page_count
    finally:
        document.close()


def check_pdf_pages(pdf_path: str | Path, max_pages: int) -> int:
    """Validate page count *before* rasterising. Returns the page count."""
    pages = count_pdf_pages(pdf_path)
    if pages < 1:
        raise InputTooLarge("PDF contains no pages")
    if pages > max_pages:
        raise InputTooLarge(
            f"PDF has {pages} pages; limit is {max_pages}. "
            "Split the document or raise OCR_MAX_PAGES."
        )
    return pages
