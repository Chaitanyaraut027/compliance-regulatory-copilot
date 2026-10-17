"""
CLI for semantic search.

Usage:  python -m app.search "your query here"
"""

from __future__ import annotations

import logging
import sys

from app.retriever import retrieve


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python -m app.search \"<your query>\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    results = retrieve(query)

    if not results:
        print("\nNo results found.")
        return

    print(f"\n═══ Search Results for: \"{query}\" ═══\n")
    for i, r in enumerate(results, 1):
        sim = r.get("similarity", 0)
        title = r.get("doc_title") or r.get("doc_filename", "?")
        pages = f"pp. {r.get('page_start', '?')}–{r.get('page_end', '?')}"
        section = r.get("section_title") or ""

        print(f"── Result {i}  (similarity: {sim:.4f}) ──")
        print(f"   Source : {title}")
        print(f"   Pages  : {pages}")
        if section:
            print(f"   Section: {section}")
        print(f"   Excerpt:")
        # Show first 400 chars of content
        content = r.get("content", "")
        preview = content[:400] + ("..." if len(content) > 400 else "")
        for line in preview.split("\n"):
            print(f"     {line}")
        print()


if __name__ == "__main__":
    main()
