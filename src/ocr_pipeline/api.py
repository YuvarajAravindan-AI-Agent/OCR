from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile

from ocr_pipeline.outputs import collect_text_outputs, list_artifacts
from ocr_pipeline.pipeline import OcrPipeline


app = FastAPI(title="OCR Pipeline", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ocr/image")
async def parse_image(file: UploadFile = File(...), mode: str = "gundam") -> dict[str, Any]:
    suffix = Path(file.filename or "input.png").suffix or ".png"
    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / f"upload{suffix}"
        input_path.write_bytes(await file.read())
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


@app.post("/v1/ocr/pdf")
async def parse_pdf(file: UploadFile = File(...), dpi: int = 300) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / (file.filename or "input.pdf")
        input_path.write_bytes(await file.read())
        output_dir = Path(tmp_dir) / "output"
        result = OcrPipeline().parse_pdf(input_path, output_dir, dpi=dpi)
        return {
            "filename": file.filename,
            "mode": result.mode,
            "pages": result.pages,
            "dpi": dpi,
            "text": collect_text_outputs(output_dir),
            "artifacts": list_artifacts(output_dir),
        }
