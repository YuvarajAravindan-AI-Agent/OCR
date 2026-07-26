from __future__ import annotations

from pathlib import Path

import typer

from ocr_pipeline.config import get_settings
from ocr_pipeline.pipeline import OcrPipeline
from ocr_pipeline.sample_docs import build_sample_documents


app = typer.Typer(help="Run the Baidu Unlimited-OCR pipeline.")


@app.command("sample-docs")
def sample_docs(output_dir: Path = typer.Option(Path("inputs"), help="Directory for generated inputs.")) -> None:
    paths = build_sample_documents(output_dir)
    for label, path in paths.items():
        typer.echo(f"{label}: {path}")


@app.command("parse-image")
def parse_image(
    image_path: Path = typer.Argument(..., exists=True, readable=True),
    output_dir: Path = typer.Option(Path("outputs/single_gundam"), help="Directory for OCR outputs."),
    mode: str = typer.Option("gundam", help="Use gundam or base."),
) -> None:
    pipeline = OcrPipeline()
    result = pipeline.parse_image(image_path, output_dir, mode=mode)
    typer.echo(f"saved: {result.output_dir}")


@app.command("parse-pdf")
def parse_pdf(
    pdf_path: Path = typer.Argument(..., exists=True, readable=True),
    output_dir: Path = typer.Option(Path("outputs/multi_page"), help="Directory for OCR outputs."),
    dpi: int = typer.Option(300, help="Rasterization DPI."),
) -> None:
    pipeline = OcrPipeline()
    result = pipeline.parse_pdf(pdf_path, output_dir, dpi=dpi)
    typer.echo(f"pages: {result.pages}")
    typer.echo(f"saved: {result.output_dir}")


@app.command("show-config")
def show_config() -> None:
    settings = get_settings()
    typer.echo(f"model_name={settings.model_name}")
    typer.echo(f"output_dir={settings.output_dir}")
    typer.echo(f"device={settings.device}")
    typer.echo(f"api_key_set={'yes' if settings.api_key else 'no'}")
    typer.echo(f"hf_token_set={'yes' if settings.hf_token else 'no'}")
