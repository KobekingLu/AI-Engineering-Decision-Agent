"""Local OCR helpers for image and scanned PDF inputs."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def is_ocr_available() -> bool:
    try:
        _ocr_engine()
        return True
    except Exception:
        return False


def ocr_image_path(path: Path) -> str:
    image = Image.open(path).convert("RGB")
    return _ocr_image_object(image)


def ocr_pdf_path(path: Path, *, max_pages: int = 8) -> str:
    doc = fitz.open(path)
    chunks: list[str] = []
    for index in range(min(doc.page_count, max_pages)):
        page = doc.load_page(index)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        page_text = _ocr_image_object(image)
        if page_text:
            chunks.append(page_text)
    return "\n\n".join(chunks).strip()


def _ocr_image_object(image: Image.Image) -> str:
    engine = _ocr_engine()
    result, _ = engine(np.array(image.convert("RGB")))
    return "\n".join(item[1] for item in (result or []) if len(item) > 1).strip()
