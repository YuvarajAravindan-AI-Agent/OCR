from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer

from ocr_pipeline.config import Settings, get_settings


def _select_dtype() -> torch.dtype:
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    if torch.cuda.is_available():
        return torch.float16
    return torch.float32


@dataclass(slots=True)
class UnlimitedOCRRuntime:
    settings: Settings
    tokenizer: object
    model: object

    @classmethod
    def load(cls, settings: Settings | None = None) -> "UnlimitedOCRRuntime":
        settings = settings or get_settings()
        if settings.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available. Set OCR_DEVICE=cpu only if the model can run on your machine.")

        dtype = _select_dtype()
        tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name,
            trust_remote_code=True,
            token=settings.hf_token,
        )
        model = AutoModel.from_pretrained(
            settings.model_name,
            trust_remote_code=True,
            use_safetensors=True,
            torch_dtype=dtype,
            token=settings.hf_token,
        )
        model = model.eval()
        if settings.device == "cuda":
            model = model.cuda()
        return cls(settings=settings, tokenizer=tokenizer, model=model)

    def infer_image(
        self,
        image_file: str | Path,
        output_dir: str | Path,
        *,
        prompt: str = "<image>document parsing.",
        base_size: int | None = None,
        image_size: int | None = None,
        crop_mode: bool = True,
        max_length: int | None = None,
        no_repeat_ngram_size: int | None = None,
        ngram_window: int | None = None,
    ) -> None:
        self.model.infer(
            self.tokenizer,
            prompt=prompt,
            image_file=str(image_file),
            output_path=str(output_dir),
            base_size=base_size or self.settings.base_size,
            image_size=image_size or self.settings.image_size,
            crop_mode=crop_mode,
            max_length=max_length or self.settings.max_length,
            no_repeat_ngram_size=no_repeat_ngram_size or self.settings.no_repeat_ngram_size,
            ngram_window=ngram_window or self.settings.ngram_window,
            save_results=True,
        )

    def infer_multi(
        self,
        image_files: list[str | Path],
        output_dir: str | Path,
        *,
        prompt: str = "<image>Multi page parsing.",
        image_size: int | None = None,
        max_length: int | None = None,
        no_repeat_ngram_size: int | None = None,
        ngram_window: int | None = None,
    ) -> None:
        self.model.infer_multi(
            self.tokenizer,
            prompt=prompt,
            image_files=[str(path) for path in image_files],
            output_path=str(output_dir),
            image_size=image_size or self.settings.image_size,
            max_length=max_length or self.settings.max_length,
            no_repeat_ngram_size=no_repeat_ngram_size or self.settings.no_repeat_ngram_size,
            ngram_window=ngram_window or 1024 if ngram_window is None else ngram_window,
            save_results=True,
        )


@lru_cache(maxsize=1)
def get_runtime() -> UnlimitedOCRRuntime:
    return UnlimitedOCRRuntime.load()
