"""Scraper. STUB. Workshop 1 block 4.

Crawl both websites, extract the readable text, and collect image
records in the same pass. Run this file directly to (re)build
data/pages.json and data/images.json.

Check for /sitemap.xml before writing a crawler. If it exists it lists
every page and you can skip the crawl entirely.
"""
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SITES = [
    # TODO: the two Inno Wing sites you were given
    "https://innowings.engg.hku.hk/innowing1/",
    "https://innowings.engg.hku.hk/innowing2/",
    "https://innoacademy.engg.hku.hk/"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}


def crawl(start_url: str, max_pages: int = 500) -> list[dict]:
    """Return every extracted page dictionary on the same site as start_url."""
    seen = set()
    queue = [start_url]
    pages = []  # Stores extracted page dicts

    domain = urlparse(start_url).netloc
    ignored_exts = (
        ".pdf", ".png", ".jpg", ".jpeg", ".gif",
        ".zip", ".mp4", ".css", ".js",
    )

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        clean_url = url.split("#")[0].rstrip("/")

        if clean_url in seen:
            continue
        seen.add(clean_url)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            # Guard: Must be 200 OK and HTML content
            if (
                resp.status_code != 200
                or "text/html" not in resp.headers.get("Content-Type", "")
            ):
                if resp.status_code != 200:
                    print(f"  [DEBUG] Status code {resp.status_code} on {url}")
                continue
            html = resp.text
        except Exception as e:
            print(f"  [DEBUG] Request failed on {url}: {e}")
            continue

        # Extract content cleanly once
        page_data = extract(html, url)
        pages.append(page_data)
        print(f"[{len(pages)}/{max_pages}] Scraped: {url}")

        # Find internal links to continue crawling
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("a[href]"):
            raw_href = a.get("href", "").strip()
            link = urljoin(url, raw_href).split("#")[0].rstrip("/")
            parsed = urlparse(link)

            if parsed.netloc == domain and link not in seen:
                if not any(parsed.path.lower().endswith(ext) for ext in ignored_exts):
                    queue.append(link)

    return pages

def extract(html: str, url: str) -> dict:
    """Return {"url", "title", "text", "images": [...]} for one page.

    Cleans boilerplate, formats HTML tables into readable text rows,
    and isolates primary content containers to improve retrieval precision.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Decompose noisy elements and site furniture
    for tag in soup(
        [
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "svg",
            "aside",
        ]
    ):
        tag.decompose()

    # 2. Convert tables into structured text so columns/cells don't get jumbled
    for table in soup.select("table"):
        rows = []
        for tr in table.select("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.select("th, td")]
            if any(cells):
                rows.append(" | ".join(cells))
        table.replace_with("\n" + "\n".join(rows) + "\n")

    # 3. Target the main content container used by WordPress/Astra/Elementor
    body = (
        soup.select_one(".entry-content")
        or soup.select_one(".post-content")
        or soup.select_one("main")
        or soup.select_one("#content")
        or soup.select_one(".content")
        or soup.select_one("article")
        or soup.body
        or soup
    )

    # 4. Extract images with absolute URLs and optional captions
    images = []
    for img in soup.select("img"):
        src = img.get("src")
        if not src:
            continue
        fig = img.find_parent("figure")
        images.append(
            {
                "src": urljoin(url, src),
                "alt": img.get("alt", ""),
                "caption": (
                    fig.find("figcaption").get_text(strip=True)
                    if fig and fig.find("figcaption")
                    else ""
                ),
                "page": url,
            }
        )

    # 5. Normalize whitespace across the extracted content
    text = " ".join(body.get_text(" ", strip=True).split())

    return {
        "url": url,
        "title": soup.title.get_text(strip=True) if soup.title else "",
        "text": text,
        "images": images,
    }


if __name__ == "__main__":
    all_pages = []
    for site in SITES:
        print(f"Crawling {site}...")
        all_pages.extend(crawl(site))

    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(all_pages, indent=1))

    images = [im for p in all_pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1))

    print(f"Done: {len(all_pages)} pages, {len(images)} images")