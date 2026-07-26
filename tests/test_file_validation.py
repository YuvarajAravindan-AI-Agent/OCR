"""File type validation: reject files by content, not extension.

Magic byte validation prevents someone from uploading virus.exe as virus.pdf.
This test suite uses python-magic to detect the actual file type.
"""

from __future__ import annotations

import pytest

from ocr_pipeline.file_validation import UnsupportedFileType, validate_file_type


class TestValidation:
    def test_accepts_valid_jpeg(self):
        # JPEG magic: ff d8 ff followed by JFIF marker
        jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01"
        assert validate_file_type(jpeg, "photo.jpg") == "image/jpeg"

    def test_accepts_valid_png(self):
        # PNG magic: 89 50 4e 47 0d 0a 1a 0a (with newlines for proper format)
        png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        assert validate_file_type(png, "photo.png") == "image/png"

    def test_accepts_valid_pdf(self):
        # PDF magic: 25 50 44 46 (minimal valid PDF)
        pdf = b"%PDF-1.4\n%EOF"
        assert validate_file_type(pdf, "doc.pdf") == "application/pdf"

    def test_rejects_empty_file(self):
        with pytest.raises(UnsupportedFileType, match="empty"):
            validate_file_type(b"", "empty.bin")

    def test_rejects_plain_text_as_pdf(self):
        # Someone uploads a .txt as .pdf
        text = b"This is just plain text, not a PDF at all"
        with pytest.raises(UnsupportedFileType, match="text/plain"):
            validate_file_type(text, "fake.pdf")

    def test_rejects_exe_renamed_to_pdf(self):
        # MZ is the PE executable signature — should be rejected
        exe_magic = b"MZ\x90\x00\x03\x00\x00\x00"
        with pytest.raises(UnsupportedFileType):
            validate_file_type(exe_magic, "notavirus.pdf")

    def test_rejects_zip_as_pdf(self):
        # ZIP magic: 50 4b 03 04 (PK) — should be rejected
        zip_magic = b"PK\x03\x04\x14\x00\x00\x00"
        with pytest.raises(UnsupportedFileType):
            validate_file_type(zip_magic, "archive.pdf")

    def test_rejects_html_masquerading_as_image(self):
        # HTML file renamed to .png
        html = b"<!DOCTYPE html><html><body>Test</body></html>"
        with pytest.raises(UnsupportedFileType, match="text/html"):
            validate_file_type(html, "notimage.png")

    def test_filename_in_error_message(self):
        # Ensure filename is in the error for context
        text = b"not a real file"
        with pytest.raises(UnsupportedFileType, match="badname.jpg"):
            validate_file_type(text, "badname.jpg")
