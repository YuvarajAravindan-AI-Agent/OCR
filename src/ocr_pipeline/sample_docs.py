from __future__ import annotations

import textwrap
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def build_sample_page(output_path: Path, page_no: int) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 1754
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _load_font(48)
    heading_font = _load_font(34)
    body_font = _load_font(26)

    draw.text((80, 70), f"Quarterly Operations Report - Page {page_no}", fill="black", font=title_font)
    draw.line([(80, 145), (width - 80, 145)], fill="black", width=3)

    body = (
        "This sample page exercises dense document parsing. It mixes paragraphs, "
        "tables, and footer notes so the OCR model has to preserve structure and "
        "reading order across the full page."
    )
    y = 190
    for line in textwrap.wrap(body, width=72):
        draw.text((80, y), line, fill="black", font=body_font)
        y += 40

    y += 30
    draw.text((80, y), f"Table {page_no}: Regional Revenue (USD, millions)", fill="black", font=heading_font)
    y += 60

    rows = [
        ["Region", "Q1", "Q2", "Q3"],
        ["North", "12.4", "13.1", "15.0"],
        ["South", "9.8", "10.2", "11.7"],
        ["East", "14.3", "13.9", "16.2"],
        ["West", "11.1", "12.5", "12.9"],
    ]
    column_width = 260
    row_height = 56
    x0 = 80

    for row_index, row in enumerate(rows):
        for column_index, cell in enumerate(row):
            x = x0 + column_index * column_width
            draw.rectangle([x, y, x + column_width, y + row_height], outline="black", width=2)
            draw.text((x + 14, y + 12), cell, fill="black", font=body_font)
        y += row_height

    y += 50
    footer = (
        f"Note {page_no}: Cross-page context is preserved when the model parses "
        "multi-page input in a single run."
    )
    for line in textwrap.wrap(footer, width=72):
        draw.text((80, y), line, fill="black", font=body_font)
        y += 40

    image.save(output_path)
    return output_path


def build_sample_pdf(page_paths: list[Path], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = fitz.open()
    try:
        for page_path in page_paths:
            image_doc = fitz.open(str(page_path))
            rect = image_doc[0].rect
            pdf_bytes = image_doc.convert_to_pdf()
            pdf_image_doc = fitz.open("pdf", pdf_bytes)
            pdf_page = pdf.new_page(width=rect.width, height=rect.height)
            pdf_page.show_pdf_page(rect, pdf_image_doc, 0)
            image_doc.close()
            pdf_image_doc.close()
        pdf.save(str(output_path))
    finally:
        pdf.close()
    return output_path


def build_sample_documents(output_dir: Path) -> dict[str, Path]:
    input_dir = output_dir
    page_1 = build_sample_page(input_dir / "sample_page_1.png", 1)
    page_2 = build_sample_page(input_dir / "sample_page_2.png", 2)
    page_3 = build_sample_page(input_dir / "sample_page_3.png", 3)
    sample_pdf = build_sample_pdf([page_1, page_2, page_3], input_dir / "sample_doc.pdf")
    return {
        "page_1": page_1,
        "page_2": page_2,
        "page_3": page_3,
        "pdf": sample_pdf,
    }
