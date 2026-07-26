from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import fitz


def pdf_to_images(pdf_path: str | Path, dpi: int = 300) -> list[Path]:
    """Rasterise a PDF to PNG images at the given DPI.

    Returns paths to PNG files in a temporary directory. The caller is
    responsible for cleaning up that directory when done.
    """
    document = fitz.open(str(pdf_path))
    tmp_dir = Path(tempfile.mkdtemp(prefix="pdf_ocr_"))
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    page_paths: list[Path] = []

    try:
        for page_number, page in enumerate(document, start=1):
            output_path = tmp_dir / f"page_{page_number:04d}.png"
            page.get_pixmap(matrix=matrix).save(str(output_path))
            page_paths.append(output_path)
    finally:
        document.close()

    return page_paths


def cleanup_rasterized_pages(page_paths: list[Path]) -> None:
    """Delete the temporary directory holding rasterised pages.

    pdf_to_images returns paths in a mkdtemp directory; this cleans it up.
    Safe to call even if pages have already been deleted or the dir is gone.
    """
    if not page_paths:
        return
    tmp_dir = page_paths[0].parent
    if tmp_dir.exists() and tmp_dir.name.startswith("pdf_ocr_"):
        shutil.rmtree(tmp_dir, ignore_errors=True)
