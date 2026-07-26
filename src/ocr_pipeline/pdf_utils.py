from __future__ import annotations

import tempfile
from pathlib import Path

import fitz


def pdf_to_images(pdf_path: str | Path, dpi: int = 300) -> list[Path]:
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
