# File_handling.py
from __future__ import annotations

from typing import Tuple
from PIL import Image, ImageOps
import docx2txt
import PyPDF2

def _clean_text(s: str) -> str:
    """Normalize whitespace and strip trailing newlines."""
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\x00", "")
    lines = [ln.rstrip() for ln in s.split("\n")]
    cleaned_lines = []
    prev_blank = False
    for ln in lines:
        is_blank = (ln.strip() == "")
        if is_blank and prev_blank:
            continue
        cleaned_lines.append(ln)
        prev_blank = is_blank
    return "\n".join(cleaned_lines).strip()

def _read_txt(uploaded_file) -> Tuple[str, str]:
    raw = uploaded_file.getvalue()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="ignore")
    return _clean_text(text), "txt"

def _read_doc_docx(uploaded_file, ext: str) -> Tuple[str, str]:
    try:
        text = docx2txt.process(uploaded_file)
        return _clean_text(text or ""), ext
    except Exception:
        msg = (
            "This .doc file could not be parsed. "
            "Please convert it to .docx or export as PDF/TXT and try again."
        )
        return msg, "unsupported"

def _read_pdf(uploaded_file) -> Tuple[str, str]:
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
    except Exception:
        return "Unable to open PDF. The file may be encrypted or corrupted.", "unsupported"

    texts = []
    for page in getattr(reader, "pages", []) or []:
        try:
            t = page.extract_text()
            if t:
                texts.append(t)
        except Exception:
            continue

    full_text = _clean_text("\n".join(texts))
    return full_text, "pdf"

def _read_image(uploaded_file, ext: str):
    img = Image.open(uploaded_file)
    try:
        img = ImageOps.exif_transpose(img)  # fix orientation
    except Exception:
        pass
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img, ext

def read_file_content(uploaded_file) -> Tuple[object, str]:
    """
    Returns (content, file_type)
      - text/docx/pdf -> content is str
      - jpg/png -> content is PIL.Image
      - unsupported -> ("Unsupported file type", "unsupported")
    """
    name = getattr(uploaded_file, "name", "") or ""
    ext = name.split(".")[-1].lower() if "." in name else ""

    if ext in ("jpg", "jpeg", "png"):
        return _read_image(uploaded_file, ext)
    if ext == "txt":
        return _read_txt(uploaded_file)
    if ext in ("doc", "docx"):
        return _read_doc_docx(uploaded_file, ext)
    if ext == "pdf":
        return _read_pdf(uploaded_file)

    return "Unsupported file type", "unsupported"
