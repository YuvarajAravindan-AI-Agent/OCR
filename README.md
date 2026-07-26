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


## Hardware requirements

`baidu/Unlimited-OCR` is a ~3.3B-parameter bfloat16 vision-language model
(DeepseekV2 MoE backbone + SAM ViT-B / CLIP-L vision encoders). **A CUDA GPU is
required in practice.**

| | |
| --- | --- |
| Weights on disk / in VRAM | 6.2 GB (bfloat16) |
| KV cache at `max_length=32768` | up to ~2 GB |
| Vision encoders with `crop_mode` | 2–3 GB transient |
| **Minimum VRAM** | **12 GB** (reduce `max_length`, disable `crop_mode`) |
| **Recommended VRAM** | **16–24 GB** — defaults work untouched |

There is no benefit to A100/H100-class hardware for a model this size.

`OCR_DEVICE=cpu` is accepted but impractical: `_select_dtype()` falls back to
float32 off-GPU, so the weights expand to ~12.4 GB of system RAM, and inference
takes minutes per page.

## Docker

The image **requires a GPU**. Without `--gpus all` the server starts and then
fails at model load with `CUDA is not available`.

```bash
docker build -t ocr-pipeline .
docker run --rm --gpus all -p 8000:8000 --env-file .env ocr-pipeline
```

To reuse an already-downloaded model instead of pulling 6.3 GB into the
container, mount the host cache:

```bash
docker run --rm --gpus all -p 8000:8000 --env-file .env \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  ocr-pipeline
```

## RunPod Serverless

OCR is bursty, so a serverless endpoint that scales to zero costs far less than
an always-on pod. `Dockerfile.runpod` builds an image around
`src/ocr_pipeline/runpod_handler.py`.

```bash
docker build -f Dockerfile.runpod -t <dockerhub-user>/ocr-pipeline-runpod:latest .
docker push <dockerhub-user>/ocr-pipeline-runpod:latest
```

Then create a Serverless endpoint pointing at that image:

- **GPU:** any 24 GB tier (RTX 4090 / L4 / A10G). 16 GB also works.
- **Network volume:** attach one at `/runpod-volume`, ~15 GB.
  `HF_HOME` is set to `/runpod-volume/huggingface` in the image, so the weights
  persist across cold starts instead of being re-downloaded each time.
- **Env:** set `HF_TOKEN` if the model repo requires authentication.

Request format:

```json
{"input": {"image_b64": "<base64 png>", "mode": "gundam"}}
{"input": {"pdf_b64": "<base64 pdf>", "dpi": 300}}
```

The response carries the parsed text inline:

```json
{"mode": "gundam", "pages": 1,
 "text": {"result.mmd": "..."},
 "artifacts": ["result.mmd", "crop_0.png"]}
```

## Tests

Run the smoke tests with:

```bash
pytest
```
