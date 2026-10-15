import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

import fitz
from PIL import Image
import pytesseract


def _configure_tesseract():
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    executable = next((path for path in candidates if path and os.path.exists(path)), None)
    if executable:
        pytesseract.pytesseract.tesseract_cmd = executable


_configure_tesseract()

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, TEMP_UPLOAD_DIR


def ensure_temp_directory():
    TEMP_UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
    return TEMP_UPLOAD_DIR


def validate_pdf_file(file_storage):
    if file_storage is None or not getattr(file_storage, "filename", None):
        raise ValueError("Please upload a PDF file.")

    filename = file_storage.filename.lower()
    if not filename.endswith(tuple(ALLOWED_EXTENSIONS)):
        raise ValueError("Only PDF files are supported.")

    file_size = 0
    if hasattr(file_storage, "content_length") and file_storage.content_length is not None:
        file_size = file_storage.content_length
    else:
        file_storage.stream.seek(0, os.SEEK_END)
        file_size = file_storage.stream.tell()
        file_storage.stream.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise ValueError("Uploaded PDF is too large. Please keep it under 10 MB.")

    return True


def extract_text_from_pdf(file_path: str) -> Dict[str, object]:
    document = fitz.open(file_path)
    passages: List[Dict[str, object]] = []
    combined_text = []

    for page_number in range(document.page_count):
        page = document[page_number]
        text = page.get_text("text")
        cleaned = " ".join(text.split())
        extraction_method = "text"
        if not cleaned:
            try:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                cleaned = " ".join(pytesseract.image_to_string(image, lang="eng").split())
                extraction_method = "ocr" if cleaned else "none"
            except (pytesseract.TesseractNotFoundError, RuntimeError) as exc:
                document.close()
                raise RuntimeError(
                    "OCR is required for this scanned PDF, but the Tesseract OCR engine is not installed."
                ) from exc
        combined_text.append(f"Page {page_number + 1}: {cleaned}")
        if cleaned:
            passages.append({
                "page_number": page_number + 1,
                "text": cleaned,
                "title": "Uploaded PDF",
                "extraction_method": extraction_method,
            })

    page_count = document.page_count
    document.close()
    full_text = "\n\n".join(combined_text)

    if not full_text.strip():
        return {
            "passages": [],
            "full_text": "",
            "page_count": page_count,
            "message": "No readable text was found in this PDF, even after OCR.",
        }

    return {
        "passages": passages,
        "full_text": full_text,
        "page_count": page_count,
        "message": "Text extracted successfully.",
    }


def save_uploaded_pdf(file_storage, session_id: str) -> str:
    ensure_temp_directory()
    path = TEMP_UPLOAD_DIR / f"{session_id}.pdf"
    file_storage.save(path)
    return str(path)


def cleanup_session_files(session_id: str):
    if not session_id:
        return
    for candidate in TEMP_UPLOAD_DIR.glob(f"{session_id}*.pdf"):
        candidate.unlink(missing_ok=True)
