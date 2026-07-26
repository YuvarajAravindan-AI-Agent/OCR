FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1             PYTHONUNBUFFERED=1             PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends             build-essential             git             libgl1             libgomp1             libmagic1             poppler-utils             && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY .env.example ./

RUN pip install --upgrade pip && pip install -e .

EXPOSE 8000

CMD ["uvicorn", "ocr_pipeline.api:app", "--host", "0.0.0.0", "--port", "8000"]
