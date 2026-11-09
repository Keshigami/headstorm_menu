"""One EasyOCR reader per process. Model weights (~100 MB) download once into ~/.EasyOCR on first use;
if that is impossible (no network) `reader()` returns None and `unavailable_reason()` says why."""
from __future__ import annotations

import os

_READER = None
_ERROR: str | None = None


def reader(allow_download: bool | None = None):
    global _READER, _ERROR
    if _READER is not None or _ERROR is not None:
        return _READER
    if allow_download is None:
        allow_download = os.getenv("EASYOCR_DOWNLOAD", "1") != "0"
    try:
        import easyocr

        _READER = easyocr.Reader(["en"], gpu=False, download_enabled=allow_download, verbose=False)
    except Exception as e:  # noqa: BLE001 - reported to the caller, tests skip on it
        _ERROR = f"{type(e).__name__}: {e}"
    return _READER


def unavailable_reason() -> str | None:
    return _ERROR


def read(image_bgr):
    """EasyOCR results as a list of (bbox, text, confidence); [] with a reason if OCR is unavailable."""
    r = reader()
    if r is None:
        raise RuntimeError(f"EasyOCR unavailable: {_ERROR}")
    return r.readtext(image_bgr)
