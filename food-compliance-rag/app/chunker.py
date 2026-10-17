"""
Text chunker — splits extracted page text into overlapping chunks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional

from app.config import get_settings


@dataclass
class Chunk:
    """A single text chunk with provenance metadata."""
    chunk_index: int
    content: str
    page_start: int
    page_end: int
    section_title: Optional[str] = None
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)


def _hash_content(text: str, index: int | None = None) -> str:
    payload = f"{index}:{text}" if index is not None else text
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _detect_section_title(text: str) -> Optional[str]:
    """
    Heuristic: look for lines that are short, mostly uppercase / title-case,
    and appear near the start of the chunk — likely a section heading.
    """
    for line in text.split("\n")[:5]:
        line = line.strip()
        if not line or len(line) > 120:
            continue
        # Lines that are ALL CAPS or Title Case and short
        if line.isupper() and 5 < len(line) < 100:
            return line
        if line.istitle() and 5 < len(line) < 100 and not line.endswith("."):
            return line
        # Match "Chapter X", "Part X", "Schedule X", "Regulation X"
        if re.match(
            r"^(Chapter|Part|Schedule|Regulation|Appendix|Annex|Section)\s",
            line, re.IGNORECASE,
        ):
            return line
    return None


def _find_break_point(text: str, target: int, window: int = 150) -> int:
    """
    Find a good split point near *target* that respects paragraph
    or sentence boundaries.
    """
    start = max(0, target - window)
    end = min(len(text), target + window)
    region = text[start:end]

    # Prefer double-newline (paragraph break)
    para_breaks = [m.start() + start for m in re.finditer(r"\n\n", region)]
    if para_breaks:
        return min(para_breaks, key=lambda p: abs(p - target))

    # Fall back to single newline
    line_breaks = [m.start() + start for m in re.finditer(r"\n", region)]
    if line_breaks:
        return min(line_breaks, key=lambda p: abs(p - target))

    # Fall back to sentence ending
    sent_breaks = [m.end() + start for m in re.finditer(r"[.;]\s", region)]
    if sent_breaks:
        return min(sent_breaks, key=lambda p: abs(p - target))

    # Last resort: exact target
    return target


def chunk_pages(
    pages: list[dict],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    """
    Chunk a list of page dicts [{"page_number": int, "text": str}]
    into overlapping text chunks.

    Parameters
    ----------
    pages : list of dicts with ``page_number`` and ``text``
    chunk_size : target chunk size in characters (default from settings)
    chunk_overlap : overlap in characters (default from settings)

    Returns
    -------
    list[Chunk]
    """
    settings = get_settings()
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    if not pages:
        return []

    # Build a single long string, recording page boundaries
    full_text = ""
    page_boundaries: list[tuple[int, int, int]] = []  # (start, end, page_number)

    for p in pages:
        start = len(full_text)
        full_text += p["text"] + "\n\n"
        end = len(full_text)
        page_boundaries.append((start, end, p["page_number"]))

    if not full_text.strip():
        return []

    chunks: list[Chunk] = []
    pos = 0
    idx = 0

    while pos < len(full_text):
        end = pos + chunk_size

        if end < len(full_text):
            end = _find_break_point(full_text, end)

        chunk_text = full_text[pos:end].strip()
        if not chunk_text:
            pos = end
            continue

        # Determine which pages this chunk spans
        page_start = None
        page_end = None
        for pb_start, pb_end, pnum in page_boundaries:
            if pb_end > pos and pb_start < end:
                if page_start is None:
                    page_start = pnum
                page_end = pnum

        section = _detect_section_title(chunk_text)

        chunks.append(Chunk(
            chunk_index=idx,
            content=chunk_text,
            page_start=page_start or 1,
            page_end=page_end or page_start or 1,
            section_title=section,
            content_hash=_hash_content(chunk_text, index=idx),
        ))

        idx += 1
        # Advance with overlap
        pos = end - chunk_overlap if end < len(full_text) else end

    return chunks
