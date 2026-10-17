"""
PDF text extraction using PyMuPDF (fitz).
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pymupdf as fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    """Extracted text for a single page."""
    page_number: int          # 1-based
    text: str
    char_count: int = 0


@dataclass
class ExtractedDocument:
    """Result of extracting a whole PDF."""
    filename: str
    filepath: str
    title: Optional[str] = None
    publication_date: Optional[str] = None
    version_info: Optional[str] = None
    page_count: int = 0
    pages: list[PageText] = field(default_factory=list)
    file_hash: str = ""
    is_empty: bool = False
    is_scanned: bool = False
    error: Optional[str] = None


def compute_file_hash(path: Path) -> str:
    """SHA-256 hash of the file for change detection."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract_date_from_filename(filename: str) -> Optional[str]:
    """Try to pull a date like 28_01_2022 from the filename."""
    m = re.search(r"(\d{2})_(\d{2})_(\d{4})", filename)
    if m:
        day, month, year = m.groups()
        return f"{year}-{month}-{day}"
    return None


def _clean_text(text: str) -> str:
    """Light cleanup without altering legal meaning."""
    # Collapse multiple spaces (but keep newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path: Path) -> ExtractedDocument:
    """
    Extract text from a PDF file.

    Returns an ExtractedDocument with per-page text.
    Flags scanned / empty PDFs clearly.
    """
    filename = path.name
    doc = ExtractedDocument(
        filename=filename,
        filepath=str(path),
        file_hash=compute_file_hash(path),
    )

    try:
        pdf = fitz.open(str(path))
    except Exception as exc:
        doc.error = f"Failed to open PDF: {exc}"
        logger.error("Cannot open %s: %s", filename, exc)
        return doc

    doc.page_count = len(pdf)

    # Try to get title from PDF metadata
    meta = pdf.metadata or {}
    doc.title = meta.get("title") or None
    if not doc.title:
        # Derive a human-readable title from the filename
        stem = path.stem.replace("_", " ")
        # Remove trailing " (1)" copies
        stem = re.sub(r"\s*\(\d+\)\s*$", "", stem)
        doc.title = stem

    # Publication date from filename
    doc.publication_date = _extract_date_from_filename(filename)

    total_chars = 0
    pages: list[PageText] = []

    for page_idx in range(len(pdf)):
        page = pdf[page_idx]
        text = page.get_text("text") or ""
        text = _clean_text(text)
        char_count = len(text)
        total_chars += char_count
        pages.append(PageText(
            page_number=page_idx + 1,
            text=text,
            char_count=char_count,
        ))

    pdf.close()

    doc.pages = pages

    if total_chars == 0:
        doc.is_empty = True
        doc.is_scanned = True
        logger.warning(
            "%s: No extractable text (%d pages). Likely scanned.",
            filename, doc.page_count,
        )
    elif total_chars < doc.page_count * 50:
        doc.is_scanned = True
        logger.warning(
            "%s: Very little text (%d chars / %d pages). Possibly scanned.",
            filename, total_chars, doc.page_count,
        )

    return doc


def extract_all_pdfs(directory: Path) -> list[ExtractedDocument]:
    """Extract text from every PDF in *directory*."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    pdfs = sorted(directory.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in %s", directory)
        return []

    results = []
    for p in pdfs:
        logger.info("Extracting: %s", p.name)
        results.append(extract_pdf(p))

    ok = sum(1 for r in results if not r.is_empty and not r.error)
    logger.info(
        "Extraction complete: %d PDFs, %d with text, %d empty/scanned, %d errors",
        len(results), ok,
        sum(1 for r in results if r.is_empty or r.is_scanned),
        sum(1 for r in results if r.error),
    )
    return results
