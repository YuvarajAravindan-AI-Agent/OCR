from pathlib import Path

import pytest

from ocr_pipeline.pipeline import OcrPipeline


class FakeRuntime:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def infer_image(self, **kwargs: object) -> None:
        self.calls.append(("infer_image", kwargs))

    def infer_multi(self, **kwargs: object) -> None:
        self.calls.append(("infer_multi", kwargs))


def test_parse_image_uses_gundam_mode(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake")
    runtime = FakeRuntime()
    pipeline = OcrPipeline(runtime=runtime)

    result = pipeline.parse_image(image_path, tmp_path / "out", mode="gundam")

    assert result.mode == "gundam"
    assert result.output_dir.exists()
    assert runtime.calls[0][0] == "infer_image"
    assert runtime.calls[0][1]["crop_mode"] is True
    assert runtime.calls[0][1]["image_size"] == 640


def test_parse_image_rejects_unknown_mode(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    image_path.write_bytes(b"fake")
    pipeline = OcrPipeline(runtime=FakeRuntime())

    with pytest.raises(ValueError, match="gundam|base"):
        pipeline.parse_image(image_path, tmp_path / "out", mode="invalid")


def test_parse_pdf_calls_multi_page_runtime(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"fake-pdf")
    runtime = FakeRuntime()
    pipeline = OcrPipeline(runtime=runtime)
    monkeypatch.setattr("ocr_pipeline.pipeline.pdf_to_images", lambda *_args, **_kwargs: [Path("page_0001.png"), Path("page_0002.png")])

    result = pipeline.parse_pdf(pdf_path, tmp_path / "out")

    assert result.mode == "multi_page"
    assert result.pages == 2
    assert runtime.calls[0][0] == "infer_multi"
    assert runtime.calls[0][1]["ngram_window"] == 1024
