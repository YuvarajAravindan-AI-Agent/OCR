from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile

from ocr_pipeline.pipeline import OcrPipeline


app = FastAPI(title="OCR Pipeline", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/ocr/image")
async def parse_image(file: UploadFile = File(...), mode: str = "gundam") -> dict[str, str | int]:
    suffix = Path(file.filename or "input.png").suffix or ".png"
    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / f"upload{suffix}"
        input_path.write_bytes(await file.read())
        output_dir = Path(tmp_dir) / "output"
        result = OcrPipeline().parse_image(input_path, output_dir, mode=mode)
        return {"input": str(result.input_path), "output_dir": str(result.output_dir), "mode": result.mode}


@app.post("/v1/ocr/pdf")
async def parse_pdf(file: UploadFile = File(...), dpi: int = 300) -> dict[str, str | int]:
    with tempfile.TemporaryDirectory(prefix="ocr_api_") as tmp_dir:
        input_path = Path(tmp_dir) / (file.filename or "input.pdf")
        input_path.write_bytes(await file.read())
        output_dir = Path(tmp_dir) / "output"
        result = OcrPipeline().parse_pdf(input_path, output_dir, dpi=dpi)
        return {"input": str(result.input_path), "output_dir": str(result.output_dir), "pages": result.pages}
