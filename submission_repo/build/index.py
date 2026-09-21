"""Indexer. STUB. Workshop 1 block 4.

Chunk the scraped text and write it to the store. Run this file
directly, after build/scrape.py, to (re)build data/chroma.

Store metadata now. Level 4 questions need to filter by year and page
type, and adding a field later means rebuilding everything.
"""
import json
from pathlib import Path
# importing reg expressions lib
import re
# imported sys to resolve the bot issue
import sys

# Add the project root (the folder above /build) to Python's module search path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.store import add_to_store, get_store

CHUNK_SIZE, OVERLAP = 800, 100

# Storing metadata now.
def detect_metadata(url: str, text: str) -> tuple[str, str]:
    """Extract page_type and year from url or content."""
    # Detecting year
    match_year = re.search(r"\b(202[0-9])\b", url) or re.search(
        r"\b(202[0-9])\b", text[:300]
    )
    year = match_year.group(1) if match_year else "unknown"

    # Detect basic category
    url_lower = url.lower()
    if any(k in url_lower for k in ["venue", "facilities", "makerspace", "lab"]):
        page_type = "venue"
    elif any(k in url_lower for k in ["equipment", "machine", "printer"]):
        page_type = "equipment"
    elif any(k in url_lower for k in ["programme", "funding", "award"]):
        page_type = "programme"
    elif "faq" in url_lower:
        page_type = "faq"
    else:
        page_type = "general"

    return year, page_type

def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Fixed-size chunks with overlap.

    Overlap exists because a fact split across a boundary is lost: a
    date at char 998 and its event name at char 1002 land in different
    chunks and neither answers the question.

    TODO try a better strategy once this works: split on headings
    TODO first, fall back to characters last, and prepend the section
    TODO heading to each chunk.
    """
    text = " ".join(text.split())
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step) if text[i:i + size].strip()]


def build_index(pages: list[dict], reset: bool = True):
    texts, metas = [], []
    for page in pages:
        # for i, piece in enumerate(chunk(page["text"])):
        #     texts.append(piece)
        year, page_type = detect_metadata(page["url"], page["text"])
        chunks = chunk(page["text"])
        for i, piece in enumerate(chunks):
            texts.append(piece)
            metas.append({
                "url":      page["url"],
                "title":    page.get("title", ""),
                "position": i,
                "kind": "text",
                # TODO add "year" and "page_type" here. Level 4 needs them.
                "year": year,
                "page_type": page_type,
            })
    print(f"Prepared {len(texts)} chunks across {len(pages)} pages.")
    store = get_store(reset=reset)
    add_to_store(store, texts, metas)
    print(f"indexed {len(texts)} chunks")
    return store


# if __name__ == "__main__":
#     pages = json.loads(Path("data/pages.json").read_text())
#     build_index(pages)

if __name__ == "__main__":
    pages_file = ROOT / "data" / "pages.json"
    pages = json.loads(pages_file.read_text(encoding="utf-8"))
    build_index(pages)