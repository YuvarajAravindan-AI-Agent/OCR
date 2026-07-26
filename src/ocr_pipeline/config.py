from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str | None = Field(default=None, validation_alias="OCR_API_KEY")
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    model_name: str = Field(default="baidu/Unlimited-OCR", validation_alias="OCR_MODEL_NAME")
    output_dir: Path = Field(default=Path("outputs"), validation_alias="OCR_OUTPUT_DIR")
    device: str = Field(default="cuda", validation_alias="OCR_DEVICE")
    image_size: int = 640
    base_size: int = 1024
    max_length: int = 32768
    no_repeat_ngram_size: int = 35
    ngram_window: int = 128


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
