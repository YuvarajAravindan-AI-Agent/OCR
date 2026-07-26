from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "src/ocr_pipeline/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow Settings(max_pages=...) as well as the env aliases, so the
        # config can be constructed directly in tests and callers.
        populate_by_name=True,
    )

    api_key: str | None = Field(default=None, validation_alias="OCR_API_KEY")
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    model_name: str = Field(default="baidu/Unlimited-OCR", validation_alias="OCR_MODEL_NAME")
    output_dir: Path = Field(default=Path("outputs"), validation_alias="OCR_OUTPUT_DIR")
    device: str = Field(default="cuda", validation_alias="OCR_DEVICE")

    # --- request limits -----------------------------------------------------
    # Secure by default: the API refuses to serve unless a key is configured.
    # Set OCR_REQUIRE_API_KEY=false for local development only.
    require_api_key: bool = Field(default=True, validation_alias="OCR_REQUIRE_API_KEY")

    # Page count is the real cost and OOM driver, not bytes: pdf_to_images
    # rasterises every page at `dpi` and infer_multi sends them all in one call.
    max_pages: int = Field(default=10, validation_alias="OCR_MAX_PAGES")
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, validation_alias="OCR_MAX_UPLOAD_BYTES")
    max_dpi: int = Field(default=400, validation_alias="OCR_MAX_DPI")

    image_size: int = 640
    base_size: int = 1024
    max_length: int = 32768
    no_repeat_ngram_size: int = 35
    ngram_window: int = 128


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
