"""Scraper. STUB. Workshop 1 block 4.

crawling both websites, extracting the readable text, and collecting image
records in the same pass. running this file directly to (re)build
data/pages.json and data/images.json.
"""

# This is a scraper that combines my previous exploration work with Punk's site-based approach.

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SITES = [
    # TODO: the two Inno Wing sites you were given
    "https://innowings.engg.hku.hk/",
    "https://innoacademy.engg.hku.hk/"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}


def crawl(start_url: str, max_pages: int = 710) -> list[dict]:
    # grabbing the domain and setting up sitemap processing
    domain = urlparse(start_url).netloc
    sitemap_url = urljoin(start_url, "/wp-sitemap.xml")
    sitemaps_to_process = [sitemap_url]
    processed_sitemaps = set()
    page_urls = []
    pages = []  # storing extracted page dicts

    print(f"fetching sitemap: {sitemap_url}")

    # looping through sitemaps to find all hidden urls first
    while sitemaps_to_process and len(page_urls) < max_pages:
        current_sitemap = sitemaps_to_process.pop(0)
        if current_sitemap in processed_sitemaps:
            continue
        processed_sitemaps.add(current_sitemap)

        try:
            # downloading the xml map
            res = requests.get(current_sitemap, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue
            
            # parsing xml content
            soup = BeautifulSoup(res.content, "xml")
            
            # looking for sub-sitemaps
            for sitemap_node in soup.find_all("sitemap"):
                loc = sitemap_node.find("loc")
                if loc and loc.text:
                    sitemaps_to_process.append(loc.text.strip())

            # extracting actual page urls
            for url_node in soup.find_all("url"):
                if len(page_urls) >= max_pages:
                    break
                loc = url_node.find("loc")
                if loc and loc.text:
                    url = loc.text.strip()
                    if urlparse(url).netloc == domain and url not in page_urls:
                        page_urls.append(url)
        except Exception:
            continue

    print(f"found {len(page_urls)} URLs, starting extraction...")

    # extracting content from the found URLs using our custom parser
    for i, url in enumerate(page_urls, 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
                page_data = extract(resp.text, url)
                pages.append(page_data)
                print(f"[{i}/{len(page_urls)}] scraped: {url}")
        except Exception as e:
            print(f"  [DEBUG] failed {url}: {e}")

    return pages

def extract(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # decomposing noisy elements and site furniture
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

    # formatting tables into structured text so columns/cells don't get jumbled
    for table in soup.select("table"):
        rows = []
        for tr in table.select("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.select("th, td")]
            if any(cells):
                rows.append(" | ".join(cells))
        table.replace_with("\n" + "\n".join(rows) + "\n")

    # targeting the main content container cz the rest is noise
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

    # collecting image records with absolute URLs and optional captions
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

    # normalizing whitespace across the extracted content
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
        print(f"crawling {site}...")
        all_pages.extend(crawl(site))

    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(all_pages, indent=1))

    images = [im for p in all_pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1))

    print(f"done: {len(all_pages)} pages, {len(images)} images")