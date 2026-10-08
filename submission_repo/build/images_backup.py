"""Image pipeline. STUB. Workshop 2 blocks 2 and 3.

Describe every collected image once, cache the result, and add the
descriptions to the same store as the scraped text. Run this file
directly, after build/scrape.py and build/index.py, to add images to
data/chroma.

Never describe an image while answering a question. Ingestion time is
unlimited; runtime is 30 seconds.
"""
import json
from pathlib import Path

import requests

import re
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from bot.llm import describe_image
from bot.store import add_to_store, get_store


DESCRIPTION_PROMPT = """
Describe the image in detail, listing in this exact order:
1. In 1-2 sentences, what the image is and what is happening (e.g. event photo, group photo, poster, workshop, lab, competition, robot, demo). Name any event, team, project or place that can be identified from visible text or any other identifying features.
2. The name of the room or area, if visible on any sign or any other description of the area.
3. The people: list each person from left to right (position, what they are doing, what they hold, and clothing only if it carries text, a logo, a number or shows a team role), then give "Total people: N". Never guess who anyone is.
4. Every distinct object, one line each. For each type of object, list each instance with its location, then give "Total: N". Count groupings in different locations separately (e.g. items on the left table vs. the items on the right table). Do not list floors, walls, ceilings or other surfaces, and do not repeat items already counted under people.
5. All visible text, copied exactly as written, in any language. Look extremely closely at all posters, whiteboards, banners, name tags, shirts, number plates and digital screens. Do not skip text just because it is small or on a screen. Never write text you cannot actually see and never fill in text from context. If you can read it but are unsure of a character or word, write your best reading followed by (uncertain). Write [unreadable] only if the text is physically impossible to make out.
6. The spatial relationships: what faces what, and what is next to what. Be highly specific. Always give left and right from the viewer's point of view.
7. The colours and materials of objects, only where distinctive.

Rules for every number: write "exactly N" only if every item is clearly visible and you counted them one by one. Write "at least N" if some are hidden, cut off or blurry. Write "about N" only if there are too many to count. Never give a bare number you are unsure about.
If you cannot tell what an object is, describe its appearance and call it "unidentified"; never guess its purpose and never use "possibly" or "likely".
Do not add closing remarks or notes after section 7. Keep the whole description under 800 words. Do not hallucinate.
"""

CACHE_PATH = Path("data/descriptions.json")


def describe_all(images: list[dict]) -> dict:
    """Describe every image once, cache the result, never regenerate.

    Ingestion is free, but not if you redo it every time you change a
    line downstream. Key the cache by image URL.
    """
    cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}

    # Aggressive whitelist approach because the LLM is expensive and slow. Only describe images that are likely to be useful.
    filtered_images = []
    for im in images:
        src = im["src"].lower()

        clean_src = src.split('?')[0] # To chop off anything after a '?'
        if not clean_src.endswith((".png", ".jpg", ".jpeg", ".webp", ".avif")):
            continue

        if any(junk in src for junk in ["logo", "icon", "thumb", "avatar", "button", "bg"]):
            continue
 
        if any(str(year) in src for year in range(2010, 2019)):
            continue

        filtered_images.append(im)

    print(f"Filtered list from {len(images)} raw links down to {len(filtered_images)} viable images.")

    for im in filtered_images[:5]:  # Limit to first 5 for now to test
        src = im["src"]

        if src in cache:
            continue
        try:
            ext = Path(src.split('?')[0]).suffix
            if not ext:
                ext = ".jpg" # Fallback just in case
                
            tmp = Path(f"data/_tmp_image{ext}")
            
            print(f"Downloading: {src[:50]}...")
            
            req = requests.get(src, timeout=30)
            req.raise_for_status()
            tmp.write_bytes(req.content)

            print("Describing with LLM...")
            result = describe_image(str(tmp), DESCRIPTION_PROMPT)
            
            # Catch empty strings before they ruin the cache
            if not result.strip():
                print(f"WARNING: LLM returned empty string for {src}")
            else:
                cache[src] = result
                CACHE_PATH.parent.mkdir(exist_ok=True)
                CACHE_PATH.write_text(json.dumps(cache, indent=1))
                print("Done and saved to disk!")
        except Exception as exc:
            print("failed:", src[:70], exc)

    print(f"{len(cache)} descriptions cached")
    return cache


def index_descriptions(descriptions: dict, images: list[dict]) -> None:
    """Add descriptions to the same store as the scraped text."""
    by_src = {im["src"]: im for im in images}
    texts, metas = [], []
    for src, text in descriptions.items():
        im = by_src.get(src, {})
        # Alt text and captions are already text and cost nothing to index.
        full = " ".join(filter(None, [im.get("alt"), im.get("caption"), text]))
        texts.append(full)

        # Getting the source page URL to check for metadata
        page_url = im.get("page", src)
        
        match_year = re.search(r"\b(202[0-9])\b", page_url) or re.search(r"\b(202[0-9])\b", full[:300])
        year = match_year.group(1) if match_year else "unknown"
        
        # If the URL or text mentions poster/workshop, flag it. Otherwise default to photo.
        page_type = "photo"
        if "poster" in page_url.lower() or "workshop" in page_url.lower() or "poster" in full.lower():
            page_type = "poster"

        metas.append({
            "url": page_url, 
            "image": src, 
            "kind": "image",
            "type": page_type,
            "year": year
        })

    store = get_store(reset=False)
    add_to_store(store, texts, metas, ids=[f"img_{i}" for i in range(len(texts))])
    print(f"indexed {len(texts)} image descriptions")


if __name__ == "__main__":
    images = json.loads(Path("data/images.json").read_text())
    descriptions = describe_all(images)
    index_descriptions(descriptions, images)
