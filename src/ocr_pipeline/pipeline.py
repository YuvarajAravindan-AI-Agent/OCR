from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ocr_pipeline.config import Settings, get_settings
from ocr_pipeline.model_runtime import UnlimitedOCRRuntime, get_runtime
from ocr_pipeline.pdf_utils import cleanup_rasterized_pages, pdf_to_images


@dataclass(slots=True)
class OcrJobResult:
    input_path: Path
    output_dir: Path
    mode: str
    pages: int = 1


class OcrPipeline:
    def __init__(self, settings: Settings | None = None, runtime: UnlimitedOCRRuntime | None = None) -> None:
        self.settings = settings or get_settings()
        self.runtime = runtime or get_runtime()

    def parse_image(
        self,
        image_path: str | Path,
        output_dir: str | Path,
        *,
        mode: str = "gundam",
        prompt: str = "<image>document parsing.",
    ) -> OcrJobResult:
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if mode == "gundam":
            self.runtime.infer_image(
                image_file=image_path,
                output_dir=output_dir,
                prompt=prompt,
                base_size=1024,
                image_size=640,
                crop_mode=True,
            )
        elif mode == "base":
            self.runtime.infer_image(
                image_file=image_path,
                output_dir=output_dir,
                prompt=prompt,
                base_size=1024,
                image_size=1024,
                crop_mode=False,
            )
        else:
            raise ValueError("mode must be either 'gundam' or 'base'")

        return OcrJobResult(input_path=image_path, output_dir=output_dir, mode=mode)

    def parse_pdf(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        *,
        dpi: int = 300,
        prompt: str = "<image>Multi page parsing.",
    ) -> OcrJobResult:
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        image_pages = pdf_to_images(pdf_path, dpi=dpi)
        try:
            self.runtime.infer_multi(
                image_files=image_pages,
                output_dir=output_dir,
                prompt=prompt,
                image_size=1024,
                ngram_window=1024,
            )
        finally:
            cleanup_rasterized_pages(image_pages)

        return OcrJobResult(input_path=pdf_path, output_dir=output_dir, mode="multi_page", pages=len(image_pages))
