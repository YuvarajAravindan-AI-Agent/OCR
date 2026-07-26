# OCR Pipeline for Baidu Unlimited-OCR

This project turns the Marktechpost tutorial into a small Python application that can:

- generate sample document pages and a sample PDF
- run single-image OCR in Gundam or Base mode
- rasterize a multi-page PDF and parse it end-to-end
- expose the same pipeline through a FastAPI service and a Typer CLI

## Setup

1. Create a virtual environment.
2. Install the package in editable mode.
3. Copy `.env.example` to `.env` and fill in any required keys.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

## API key placeholder

The codebase reads `OCR_API_KEY` from the environment through the settings layer in `src/ocr_pipeline/config.py`. The tutorial uses a local Hugging Face model load, so the API key is optional unless you later connect the app to a hosted model endpoint or gateway.

## CLI examples

Generate sample inputs:

```bash
ocr-pipeline sample-docs --output-dir inputs
```

Parse a document image:

```bash
ocr-pipeline parse-image inputs/sample_page_1.png --mode gundam
```

Parse a PDF:

```bash
ocr-pipeline parse-pdf inputs/sample_doc.pdf
```

## API examples

Run the server:

```bash
uvicorn ocr_pipeline.api:app --reload
```

Available routes:

- `GET /healthz`
- `POST /v1/ocr/image`
- `POST /v1/ocr/pdf`


## Docker

Build the container image:

```bash
docker build -t ocr-pipeline .
```

Run the API:

```bash
docker run --rm -p 8000:8000 --env-file .env ocr-pipeline
```

## Tests

Run the smoke tests with:

```bash
pytest
```
