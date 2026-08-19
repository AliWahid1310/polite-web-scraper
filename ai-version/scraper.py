"""
Quarantined AI Version Scraper.
Built automatically from prompt specification to compare against hand-crafted pipeline.
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urljoin
from typing import Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, ValidationError

BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "PoliteWebScraper/1.0 (+https://github.com/AliWahid1310/polite-web-scraper)"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class AIBookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(..., gt=0.0)
    availability_text: str
    stock_count: int = Field(..., ge=0)
    rating_text: str
    rating: int = Field(..., ge=1, le=5)
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: datetime


def cache_key(url: str) -> str:
    h = hashlib.md5(url.encode()).hexdigest()[:12]
    return os.path.join(CACHE_DIR, f"{h}.html")


def ai_fetch(url: str) -> tuple[str | None, bool]:
    path = cache_key(url)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), True

    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        if r.status_code != 200:
            return None, False
        html = r.text
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        time.sleep(0.5)
        return html, False
    except Exception:
        return None, False


def run_ai_scraper():
    start = datetime.now(timezone.utc)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    urls = []
    curr = BASE_URL
    pages = 0
    cache_hits = 0
    
    # 1. Crawl
    while curr and pages < 3:
        pages += 1
        html, hit = ai_fetch(curr)
        if hit: cache_hits += 1
        if not html: break
        soup = BeautifulSoup(html, "lxml")
        for pod in soup.select("article.product_pod"):
            a = pod.select_one("h3 > a")
            if a and a.get("href"):
                urls.append((urljoin(curr, a["href"]), curr))
        next_tag = soup.select_one("li.next > a")
        curr = urljoin(curr, next_tag["href"]) if next_tag else None

    # 2. Extract & Validate
    valid = []
    errors = []
    seen = set()
    failed = 0

    for book_url, src in urls:
        if book_url in seen: continue
        seen.add(book_url)
        
        html, hit = ai_fetch(book_url)
        if hit: cache_hits += 1
        if not html:
            failed += 1
            continue

        soup = BeautifulSoup(html, "lxml")
        title = soup.select_one("div.product_main h1")
        price = soup.select_one("p.price_color")
        avail = soup.select_one("p.instock.availability")
        rating_elem = soup.select_one("p.star-rating")
        
        rating_cls = "Unknown"
        if rating_elem:
            for c in rating_elem.get("class", []):
                if c in RATING_MAP:
                    rating_cls = c
                    break

        desc_elem = soup.select_one("#product_description ~ p")
        desc = desc_elem.get_text(strip=True) if desc_elem else None

        p_match = re.search(r"(\d+\.\d+)", price.get_text() if price else "")
        price_val = float(p_match.group(1)) if p_match else 0.0

        st_match = re.search(r"\((\d+)\s+available\)", avail.get_text() if avail else "")
        stock_val = int(st_match.group(1)) if st_match else (1 if avail and "in stock" in avail.get_text().lower() else 0)

        raw = {
            "title": title.get_text(strip=True) if title else "",
            "product_url": book_url,
            "price_text": price.get_text(strip=True) if price else "",
            "price_gbp": price_val,
            "availability_text": " ".join(avail.get_text().split()) if avail else "",
            "stock_count": stock_val,
            "rating_text": rating_cls,
            "rating": RATING_MAP.get(rating_cls, 0),
            "description": desc,
            "source_page": src,
            "fetched_at": datetime.now(timezone.utc),
        }

        try:
            rec = AIBookRecord(**raw)
            valid.append(rec)
        except ValidationError as e:
            errors.append({"raw": raw, "errors": str(e)})

    # Store
    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump([v.model_dump(mode="json") for v in valid], f, indent=2)

    with open(os.path.join(OUTPUT_DIR, "run-report.json"), "w", encoding="utf-8") as f:
        json.dump({
            "start_time": start.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat(),
            "catalogue_pages": pages,
            "valid_records": len(valid),
            "failed_pages": failed,
            "cache_hits": cache_hits,
        }, f, indent=2)

    print(f"AI Scraper Finished: valid={len(valid)}, errors={len(errors)}, failed={failed}")


if __name__ == "__main__":
    run_ai_scraper()
