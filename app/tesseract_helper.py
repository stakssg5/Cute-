import os
import shutil
from typing import Optional


def find_tesseract_path() -> Optional[str]:
    """Try to locate tesseract executable from common locations.

    Users can override by setting env var TESSERACT_PATH.
    """
    override = os.environ.get("TESSERACT_PATH")
    if override and os.path.exists(override):
        return override

    # PATH lookup
    path = shutil.which("tesseract")
    if path:
        return path

    # Windows typical install paths
    candidates = [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    return None
