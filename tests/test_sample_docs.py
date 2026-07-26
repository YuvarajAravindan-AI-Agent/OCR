from pathlib import Path

from ocr_pipeline.sample_docs import build_sample_documents


def test_build_sample_documents(tmp_path: Path) -> None:
    outputs = build_sample_documents(tmp_path)

    assert outputs["page_1"].exists()
    assert outputs["page_2"].exists()
    assert outputs["page_3"].exists()
    assert outputs["pdf"].exists()
    assert outputs["pdf"].suffix == ".pdf"
