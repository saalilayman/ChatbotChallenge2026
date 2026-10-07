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

from bot.llm import describe_image
from bot.store import add_to_store, get_store

DESCRIPTION_PROMPT = """
Describe the image in detail, listing in this exact order:
1. In 1-2 sentences, what the image is and what is happening (e.g. event photo, group photo, poster, workshop, lab, competition, robot, demo). Name any event, team, project or place that can be identified from visible text or any other identifying features.
2. The name of the room or area, if visible on any sign or any other description of the area.
3. The people: list each person from left to right (position, what they are doing, what they hold, and clothing only if it carries text, a logo, a number or shows a team role), then give "Total people: N". Never guess who anyone is. Make sure you count the total number of people correctly, despite people being hidden behind objects/slightly out of frame. If you believe there are people who are obscured, you may give a range of people that might be present.
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

    for im in images:
        src = im["src"]
        if src in cache:
            continue
        try:
            tmp = Path("data/_tmp_image")
            tmp.write_bytes(requests.get(src, timeout=30).content)
            cache[src] = describe_image(str(tmp), DESCRIPTION_PROMPT)
        except Exception as exc:
            print("failed:", src[:70], exc)

    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=1))
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
        metas.append({"url": im.get("page", src), "image": src, "kind": "image"})
    store = get_store(reset=False)
    add_to_store(store, texts, metas, ids=[f"img_{i}" for i in range(len(texts))])
    print(f"indexed {len(texts)} image descriptions")


if __name__ == "__main__":
    images = json.loads(Path("data/images.json").read_text())
    images_test = [
 {
  "src": "https://innoacademy.engg.hku.hk/wp-content/uploads/2026/04/24e4e318-1c77-48ad-9c37-affb39cc1c74-768x432.jpg",
  "alt": "Our SRA team won the HKAE Pitch Competition with the project ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals, developed as part of Innovation Academy's initiative for social work training.",
  "caption": "Our SRA team won the HKAE Pitch Competition with the project ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals, developed as part of Innovation Academy's initiative for social work training.",
  "page": "https://innoacademy.engg.hku.hk/"
 },
  {
  "src": "https://innoacademy.engg.hku.hk/wp-content/uploads/2019/05/DSC07235-1-768x432.jpg",
  "alt": "DSC07235 1",
  "caption": "",
  "page": "https://innoacademy.engg.hku.hk/innoshow4/notes-to-showcasing-team/"
 },
 {
  "src": "https://innoacademy.engg.hku.hk/wp-content/uploads/2021/09/2021_Pitching-for-TPg_Poster_final-1024x683.jpg",
  "alt": "",
  "caption": "",
  "page": "https://innoacademy.engg.hku.hk/tpg_pitching_2021/"
 },
{"src": "https://innowings.engg.hku.hk/wp-content/uploads/2026/07/DSC00316-scaled.jpg",
  "alt": "",
  "caption": "",
  "page": "https://innowings.engg.hku.hk/nano/"
},
{"src":"https://innowings.engg.hku.hk/wp-content/uploads/2025/11/Image-49-1536x1152.jpg"},
 {
  "src": "https://innoacademy.engg.hku.hk/wp-content/uploads/2025/09/Robot-arm-challenge-Fall-2025-A2-Landscape-3-1024x724.png",
  "alt": "",
  "caption": "",
  "page": "https://innoacademy.engg.hku.hk/2025_robotic_workshop_1/"
 },
 {"src":"https://innoacademy.engg.hku.hk/wp-content/uploads/2024/12/UNSW-768x576.jpeg"},
 {"src":"https://innoacademy.engg.hku.hk/wp-content/uploads/2023/02/IMG_0818-scaled.jpg"},
 {"src":"https://innowings.engg.hku.hk/wp-content/uploads/2019/08/sksinn20230503122-1536x1024.jpg"},
 {"src":"https://innowings.engg.hku.hk/wp-content/uploads/2023/08/20250413_010413039_iOS-scaled.jpg"}
    ]

    images_test_2 = [
     {"src":"https://innoacademy.engg.hku.hk/wp-content/uploads/2024/12/UNSW-768x576.jpeg"},
 {"src":"https://innoacademy.engg.hku.hk/wp-content/uploads/2023/02/IMG_0818-scaled.jpg"},
    ]
    
    descriptions = describe_all(images_test_2)
    index_descriptions(descriptions, images_test_2)
