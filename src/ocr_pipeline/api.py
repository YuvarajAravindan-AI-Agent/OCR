from __future__ import annotations

import secrets
import tempfile
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile

from ocr_pipeline.config import Settings, get_settings
from ocr_pipeline.limits import InputTooLarge, check_dpi, check_pdf_pages, check_upload_size
from ocr_pipeline.outputs import collect_text_outputs, list_artifacts
from ocr_pipeline.pipeline import OcrPipeline

app = FastAPI(title="OCR Pipeline", version="0.2.0")

READ_CHUNK = 1024 * 1024


def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Reject unauthenticated calls.

    Secure by default: if OCR_REQUIRE_API_KEY is left on but no key is
    configured, refuse to serve rather than silently running open.

    Settings arrive via Depends (not get_settings() directly) so the whole
    auth path is overridable and testable.
    """
    if not settings.require_api_key:
        return
    if not settings.api_key:
        raise HTTPException(
            status_code=500,
            detail="server misconfigured: OCR_API_KEY is unset while OCR_REQUIRE_API_KEY is true",
        )
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="invalid or missing X-API-Key")


async def read_capped(file: UploadFile, max_bytes: int) -> bytes:
    """Read an upload without letting an oversized body into memory."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise InputTooLarge(
                f"upload exceeds {max_bytes} bytes ({max_bytes // (1024 * 1024)} MB)"
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    check_upload_size(len(data), max_bytes)
    return data


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/limits")
def limits(settings: Settings = Depends(get_settings)) -> dict[str, int | bool]:
    """Published limits, so a client can validate before uploading."""
    return {
        "max_upload_bytes": settings.max_upload_bytes,
        "max_pages": settings.max_pages,
        "max_dpi": settings.max_dpi,
        "api_key_required": settings.require_api_key,
    }


@app.post("/v1/ocr/image", dependencies=[Depends(require_api_key)])
async def parse_image(
    file: UploadFile = File(...),
    mode: str = "gundam",
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    if mode not in {"gundam", "base"}:
        raise HTTPException(status_code=422, detail="mode must be 'gundam' or 'base'")

    suffix = Path(file.filename or "input.png").suffix or ".png"
    try:
        data = await read_capped(file, settings.max_upload_bytes)
    except InputTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / f"upload{suffix}"
        input_path.write_bytes(data)
        output_dir = Path(tmp_dir) / "output"
        result = OcrPipeline().parse_image(input_path, output_dir, mode=mode)
        # Read results out before the temp directory is removed on context exit.
        return {
            "filename": file.filename,
            "mode": result.mode,
            "pages": result.pages,
            "text": collect_text_outputs(output_dir),
            "artifacts": list_artifacts(output_dir),
        }


@app.post("/v1/ocr/pdf", dependencies=[Depends(require_api_key)])
async def parse_pdf(
    file: UploadFile = File(...),
    dpi: int = 300,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    try:
        check_dpi(dpi, settings.max_dpi)
        data = await read_capped(file, settings.max_upload_bytes)
    except InputTooLarge as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / (Path(file.filename or "input.pdf").name)
        input_path.write_bytes(data)
        output_dir = Path(tmp_dir) / "output"

        # Reject page-heavy PDFs before rasterising anything.
        try:
            check_pdf_pages(input_path, settings.max_pages)
        except InputTooLarge as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc

        result = OcrPipeline().parse_pdf(input_path, output_dir, dpi=dpi)
        return {
            "filename": file.filename,
            "mode": result.mode,
            "pages": result.pages,
            "dpi": dpi,
            "text": collect_text_outputs(output_dir),
            "artifacts": list_artifacts(output_dir),
        }
