from __future__ import annotations

from pathlib import Path

# The model writes its parsed output with save_results=True. Filenames are
# decided by the upstream modelling code, so collect whatever text it produced
# rather than assuming a specific name.
TEXT_SUFFIXES = {".mmd", ".md", ".txt", ".json", ".html"}

MAX_INLINE_BYTES = 5_000_000


def collect_text_outputs(output_dir: str | Path) -> dict[str, str]:
    """Read the model's text artefacts out of output_dir.

    Must be called before the caller's temporary directory is torn down.
    """
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        return {}

    results: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_INLINE_BYTES:
                results[str(path.relative_to(output_dir))] = (
                    f"<omitted: {path.stat().st_size} bytes exceeds inline limit>"
                )
                continue
            results[str(path.relative_to(output_dir))] = path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError as exc:
            results[str(path.relative_to(output_dir))] = f"<unreadable: {exc}>"

    return results


def list_artifacts(output_dir: str | Path) -> list[str]:
    """Every file the model produced, including images it may have cropped."""
    output_dir = Path(output_dir)
    if not output_dir.is_dir():
        return []
    return sorted(
        str(p.relative_to(output_dir)) for p in output_dir.rglob("*") if p.is_file()
    )
