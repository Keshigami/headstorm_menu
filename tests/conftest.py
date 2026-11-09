from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def samples() -> Path:
    from menusync.samples import generate

    out = HERE / "samples"
    if len(list(out.glob("menu_*.png"))) < 5 or not (out / "ground_truth.json").exists():
        generate(out, 5)
    return out


@pytest.fixture(scope="session")
def ocr_ready():
    """Skip, with the reason, when EasyOCR cannot load or download its model (offline first run)."""
    from menusync.ocr import reader, unavailable_reason

    if reader() is None:
        pytest.skip(f"EasyOCR model unavailable (download not possible?): {unavailable_reason()}")
    return True
