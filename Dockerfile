# GPU image. The model is a ~3.3B bfloat16 VLM and will not run usefully on CPU.
#
# The CUDA base supplies the userspace driver plumbing; the torch wheel from PyPI
# bundles its own CUDA runtime libraries, so we do not install a CUDA toolkit here.
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Keep weights on a mounted volume so cold starts do not re-download 6.3 GB.
    HF_HOME=/runpod-volume/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3-pip \
        build-essential \
        git \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libmagic1 \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY .env.example ./

RUN python -m pip install --upgrade pip && python -m pip install -e .

EXPOSE 8000

# NOTE: this container REQUIRES a GPU. Run it with --gpus all, e.g.
#   docker run --rm --gpus all -p 8000:8000 --env-file .env ocr-pipeline
# Without --gpus all the server starts but every request fails at model load
# with "CUDA is not available" (see src/ocr_pipeline/model_runtime.py).
CMD ["uvicorn", "ocr_pipeline.api:app", "--host", "0.0.0.0", "--port", "8000"]
