"""Extracts plain text from uploaded resume/job files (PDF, DOCX)."""

from __future__ import annotations

import io

ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text(file_storage) -> str:
    """Takes a Flask/Werkzeug FileStorage object and returns extracted plain text."""
    filename = (file_storage.filename or "").lower()

    if filename.endswith(".pdf"):
        return _extract_pdf(file_storage)
    if filename.endswith(".docx"):
        return _extract_docx(file_storage)

    raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def _extract_pdf(file_storage) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(file_storage.read()))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    if not text.strip():
        raise ValueError("Couldn't read any text from that PDF. It may be a scanned image.")
    return text


def _extract_docx(file_storage) -> str:
    import docx

    document = docx.Document(io.BytesIO(file_storage.read()))
    text = "\n".join(p.text for p in document.paragraphs)
    if not text.strip():
        raise ValueError("Couldn't read any text from that DOCX file.")
    return text