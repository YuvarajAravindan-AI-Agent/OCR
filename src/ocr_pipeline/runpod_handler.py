"""RunPod Serverless entrypoint.

Expects a job payload of:

    {"input": {"image_b64": "<base64>", "mode": "gundam"}}
    {"input": {"pdf_b64":   "<base64>", "dpi": 300}}

Returns the parsed text inline. The model is loaded once per worker on the
first request and then reused for the life of that worker, so keep workers
warm if latency matters.
"""

from __future__ import annotations

import base64
import binascii
import tempfile
import traceback
from pathlib import Path
from typing import Any

import runpod

from ocr_pipeline.config import get_settings
from ocr_pipeline.limits import InputTooLarge, check_dpi, check_pdf_pages, check_upload_size
from ocr_pipeline.outputs import collect_text_outputs, list_artifacts
from ocr_pipeline.pipeline import OcrPipeline


def _decode(value: str, field: str, max_bytes: int) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field} is not valid base64: {exc}") from exc
    check_upload_size(len(raw), max_bytes)
    return raw


def _warm() -> OcrPipeline:
    # Constructing OcrPipeline resolves get_runtime(), which is lru_cached —
    # the weights load once per worker process.
    return OcrPipeline()


def handler(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("input") or {}
    settings = get_settings()
    dpi = int(payload.get("dpi", 300))

    try:
        if "image_b64" in payload:
            data = _decode(payload["image_b64"], "image_b64", settings.max_upload_bytes)
            mode = payload.get("mode", "gundam")
            if mode not in {"gundam", "base"}:
                raise ValueError("mode must be 'gundam' or 'base'")
            suffix = payload.get("suffix", ".png")
            kind = "image"
        elif "pdf_b64" in payload:
            data = _decode(payload["pdf_b64"], "pdf_b64", settings.max_upload_bytes)
            check_dpi(dpi, settings.max_dpi)
            suffix = ".pdf"
            kind = "pdf"
        else:
            return {"error": "provide either image_b64 or pdf_b64 in input"}
    except (ValueError, InputTooLarge) as exc:
        return {"error": str(exc)}

    try:
        with tempfile.TemporaryDirectory(prefix="ocr_rp_") as tmp_dir:
            input_path = Path(tmp_dir) / f"upload{suffix}"
            input_path.write_bytes(data)
            output_dir = Path(tmp_dir) / "output"

            pipeline = _warm()
            if kind == "image":
                result = pipeline.parse_image(input_path, output_dir, mode=mode)
            else:
                # Reject page-heavy PDFs before rasterising anything.
                try:
                    check_pdf_pages(input_path, settings.max_pages)
                except InputTooLarge as exc:
                    return {"error": str(exc)}
                result = pipeline.parse_pdf(input_path, output_dir, dpi=dpi)

            # Collect before the temp directory disappears.
            return {
                "mode": result.mode,
                "pages": result.pages,
                "text": collect_text_outputs(output_dir),
                "artifacts": list_artifacts(output_dir),
            }
    except Exception as exc:  # surfaced to the caller instead of a bare 500
        return {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}


runpod.serverless.start({"handler": handler})
