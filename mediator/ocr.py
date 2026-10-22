"""Local OCR and field extraction for synthetic medicine-label images."""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any


def extract_label_fields(image_bytes: bytes) -> dict[str, Any]:
    """Run Tesseract OCR on an uploaded image and parse labelled fields.

    Tesseract itself must be installed on the machine (e.g. `apt install
    tesseract-ocr`) and `pytesseract`/Pillow installed in the Python venv.
    The raw OCR text is always returned, even when not all fields are found.
    """
    try:
        from PIL import Image, ImageEnhance, ImageOps
        import pytesseract
    except ImportError as exc:
        raise RuntimeError("OCR Python dependencies are missing. Install requirements.txt in the active venv.") from exc

    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.5)
        # Avoid unbounded memory use for unexpectedly large uploads.
        max_dimension = 2400
        if max(image.size) > max_dimension:
            scale = max_dimension / max(image.size)
            image = image.resize((int(image.width * scale), int(image.height * scale)))
        raw_text = pytesseract.image_to_string(image, config="--psm 6")
    except Exception as exc:
        raise RuntimeError(f"Could not read the uploaded image with OCR: {exc}") from exc

    parsed = parse_label_text(raw_text)
    parsed["raw_ocr_text"] = raw_text
    return parsed


def _match_line(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip(" \t:;-|") if match else None


def parse_label_text(raw_text: str) -> dict[str, Any]:
    """Extract likely label fields from line-labelled synthetic packaging text."""
    text = raw_text or ""
    item_code = _match_line(
        text,
        r"^\s*(?:ITEM\s*CODE|PRODUCT\s*CODE|ITEM\s*ID|CODE)\s*[:#=-]?\s*([A-Z0-9OILQ][A-Z0-9OILQ\s-]{2,24})\s*$",
    )
    if item_code:
        item_code = re.sub(r"[\s-]", "", item_code).upper()
    else:
        code_match = re.search(r"\bMED[\s-]*[A-Z0-9OILQ]{4,8}\b", text, flags=re.IGNORECASE)
        item_code = re.sub(r"[\s-]", "", code_match.group(0)).upper() if code_match else None

    product_name = _match_line(text, r"^\s*(?:PRODUCT(?:\s*NAME)?|MEDICINE(?:\s*NAME)?)\s*[:=-]\s*(.+?)\s*$")
    batch_no = _match_line(text, r"^\s*BATCH(?:\s*(?:NO\.?|NUMBER|#))?\s*[:=-]\s*([A-Z0-9-]+)\s*$")
    manufacturer = _match_line(text, r"^\s*(?:MANUFACTURER|MFR|MADE\s*BY)\s*[:=-]\s*(.+?)\s*$")
    expiry_date = _match_line(text, r"^\s*(?:EXPIRY(?:\s*DATE)?|EXP\.?\s*DATE|USE\s*BY)\s*[:=-]\s*([A-Z0-9./-]+)\s*$")
    return {
        "observed_item_code": item_code,
        "observed_product_name": product_name,
        "observed_batch_no": batch_no,
        "observed_manufacturer": manufacturer,
        "observed_expiry_date": expiry_date,
    }
