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
    "https://innowings.engg.hku.hk/",
    "https://innoacademy.engg.hku.hk/"
]

"""
def crawl(start_url: str, max_pages: int = 500) -> list[str]:
    seen, queue, out = set(), [start_url], []
    domain = urlparse(start_url).netloc

    while queue and len(out) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            html = requests.get(url, timeout=20).text
        except Exception:
            continue
        out.append(url)

        # TODO find the links on this page and add the internal ones to
        # TODO queue, something like:
        # for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        #     link = urljoin(url, a["href"]).split("#")[0]
        #     if urlparse(link).netloc == domain and link not in seen:
        #         queue.append(link)

    return out
"""

def crawl_from_sitemap(
    sitemap_url: str = "https://innowings.engg.hku.hk/wp-sitemap.xml",
    max_pages: int = 710,
    save_path: str | Path | None = None,
) -> list[str]:

    domain = urlparse(sitemap_url).netloc
    sitemaps_to_process = [sitemap_url]
    processed_sitemaps = set()
    page_urls = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    while sitemaps_to_process and len(page_urls) < max_pages:
        current_sitemap = sitemaps_to_process.pop(0)

        if current_sitemap in processed_sitemaps:
            continue
        processed_sitemaps.add(current_sitemap)

        try:
            res = requests.get(current_sitemap, headers=headers, timeout=15)
            if res.status_code != 200:
                continue

            # Parse XML with BeautifulSoup
            soup = BeautifulSoup(res.content, "xml")

            # looking for sub-sitemaps
            for sitemap_node in soup.find_all("sitemap"):
                loc = sitemap_node.find("loc")
                if loc and loc.text:
                    sitemaps_to_process.append(loc.text.strip())

            # looking for actual page urls
            for url_node in soup.find_all("url"):
                if len(page_urls) >= max_pages:
                    break

                loc = url_node.find("loc")
                if loc and loc.text:
                    url = loc.text.strip()
                    # Verify domain and check duplicates
                    if urlparse(url).netloc == domain and url not in page_urls:
                        page_urls.append(url)

        except Exception:
            continue

    return page_urls

def extract(html: str, url: str) -> dict:
    """Return {"url", "title", "text", "images": [...]} for one page.

    soup.get_text() on the whole page returns the navigation menu and
    footer on every page. Those near-identical fragments become chunks
    that look moderately similar to every query and crowd real results
    out of your top five. Open the site, right-click the content, choose
    Inspect, and find the element that actually wraps it.
    """
    soup = BeautifulSoup(html, "html.parser")

    # TODO replace this with the element that holds the content, e.g.
    # TODO soup.select_one("main") or soup.select_one("#content")
    body = soup.select_one("#content")

    images = []
    for img in soup.select("img"):
        src = img.get("src")
        if not src:
            continue
        fig = img.find_parent("figure")
        images.append({
            "src":     urljoin(url, src),     # relative -> absolute
            "alt":     img.get("alt", ""),
            "caption": (fig.find("figcaption").get_text(strip=True)
                        if fig and fig.find("figcaption") else ""),
            "page":    url,
        })

    return {
        "url":    url,
        "title":  soup.title.get_text(strip=True) if soup.title else "",
        "text":   body.get_text(" ", strip=True),
        "images": images,
    }


if __name__ == "__main__":
    pages = []
    for site in SITES:
        for url in crawl_from_sitemap(site + "wp-sitemap.xml"):
            try:
                pages.append(extract(requests.get(url, timeout=20).text, url))
            except Exception as exc:
                print("skipped", url, exc)

    
    Path("data").mkdir(exist_ok=True)
    Path("data/pages.json").write_text(json.dumps(pages, indent=1))

    images = [im for p in pages for im in p["images"]]
    Path("data/images.json").write_text(json.dumps(images, indent=1))

    print(f"{len(pages)} pages, {len(images)} images")
