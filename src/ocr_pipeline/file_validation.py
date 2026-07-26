"""File type validation by magic bytes, not extension.

An attacker can rename virus.exe to invoice.pdf. We reject based on actual
file content (magic bytes), not trusting the extension.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

try:
    import magic

    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False


class UnsupportedFileType(ValueError):
    """Raised when a file's actual type does not match what we accept."""


# MIME types we accept.
ACCEPTED_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

# Magic byte signatures. If python-magic is unavailable, fall back to these.
# Format: (bytes, name, mime)
MAGIC_SIGS = [
    (b"\xff\xd8\xff", "JPEG", "image/jpeg"),
    (b"\x89PNG", "PNG", "image/png"),
    (b"RIFF", "WEBP", "image/webp"),  # RIFF ...WEBP
    (b"%PDF", "PDF", "application/pdf"),
]


def _mime_from_magic(data: bytes) -> str | None:
    """Use python-magic if available, else fall back to magic byte sigs."""
    if HAS_MAGIC:
        try:
            mime = magic.from_buffer(data, mime=True)
            return mime if isinstance(mime, str) else None
        except Exception:
            pass

    # Fallback: check magic byte signatures.
    for sig_bytes, name, mime in MAGIC_SIGS:
        if data.startswith(sig_bytes):
            if mime == "image/webp":
                # WEBP is RIFF ...WEBP; just verify it's not something else.
                if b"WEBP" in data[:100]:
                    return mime
            else:
                return mime
    return None


def validate_file_type(file_data: bytes, filename: str) -> str:
    """Check that a file's actual type is accepted.

    Args:
        file_data: The raw bytes of the uploaded file.
        filename: The filename (used only for error messages).

    Returns:
        The MIME type (e.g., "image/png", "application/pdf").

    Raises:
        UnsupportedFileType if the file is not actually an image or PDF.
    """
    if not file_data:
        raise UnsupportedFileType("file is empty")

    mime = _mime_from_magic(file_data)
    if not mime:
        raise UnsupportedFileType(
            f"{filename}: could not determine file type "
            "(must be JPEG, PNG, WebP, or PDF)"
        )

    if mime not in ACCEPTED_MIMES:
        raise UnsupportedFileType(
            f"{filename}: type is {mime}; "
            f"accepted types are {', '.join(sorted(ACCEPTED_MIMES))}"
        )

    return mime


def file_type_from_mime(mime: str) -> str:
    """Map MIME type to a file extension for use in temporary paths."""
    return mimetypes.guess_extension(mime) or ".bin"
