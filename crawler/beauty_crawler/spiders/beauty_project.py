"""
TheBeautyProject.gr spider — специализированный beauty-каталог Греции.

Структура сайта (WordPress):
  Листинг: https://thebeautyproject.gr/en/businesses/page/{N}/
  Детальная: https://thebeautyproject.gr/en/businesses/{slug}/

62+ страниц листинга. Каждый бизнес: название, категории услуг, адрес, телефон,
описание, фото, социальные сети.

Run standalone:
  python -m beauty_crawler.spiders.beauty_project
"""
import logging
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Salon, Photo, SocialLink, CrawlerSource, get_session
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

BASE         = "https://thebeautyproject.gr"
LISTING_BASE = f"{BASE}/en/businesses"
MAX_PAGES    = 100  # site currently ~62 pages; cap for safety

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,el;q=0.8",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
def fetch(url: str) -> BeautifulSoup:
    resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_listing_page(page: int) -> BeautifulSoup:
    url = f"{LISTING_BASE}/page/{page}/" if page > 1 else f"{LISTING_BASE}/"
    return fetch(url)


def extract_detail_urls(soup: BeautifulSoup) -> list[str]:
    urls = []
    # WordPress loop items — article or .post or .business-item links
    for a in soup.select("article a[href], .business-card a[href], h2.entry-title a, .post a.more-link"):
        href = a.get("href", "")
        if "/businesses/" in href and href not in urls:
            full = urljoin(BASE, href)
            # Exclude pagination and archive links
            if "page/" not in full and full != f"{LISTING_BASE}/":
                urls.append(full)
    return urls


def page_has_content(soup: BeautifulSoup) -> bool:
    return bool(soup.select("article, .business-card, .business-item, .post"))


def parse_detail(soup: BeautifulSoup, url: str) -> dict | None:
    data: dict = {"source_url": url}

    # Name — WordPress h1.entry-title or page title
    name_el = soup.select_one("h1.entry-title, h1.page-title, h1.business-title, h1")
    if not name_el:
        return None
    data["name"] = name_el.get_text(strip=True)
    if not data["name"] or data["name"].lower() in ("businesses", "home"):
        return None

    # Description
    desc_el = soup.select_one(".entry-content p, .business-description, .about-text")
    if desc_el:
        data["description"] = desc_el.get_text(strip=True)

    # Contact info — often in a sidebar or contact block
    text = soup.get_text(" ", strip=True)

    # Phone
    phones = []
    for el in soup.select("a[href^='tel:'], [itemprop=telephone]"):
        ph = re.sub(r"[^\d+]", "", el.get("href", "").replace("tel:", "") or el.get_text())
        if ph and len(ph) >= 8:
            phones.append(ph)
    if not phones:
        # Fallback: regex on page text (Greek landline 2xx or mobile 69x)
        found = re.findall(r"(?:\+30\s*)?(?:69\d|2\d{2})\s*\d{3}\s*\d{4}", text)
        phones = [re.sub(r"\s", "", p) for p in found]
    if phones:
        data["phone_primary"]   = phones[0]
        data["phone_secondary"] = phones[1] if len(phones) > 1 else None

    # Address
    addr_el = soup.select_one("[itemprop=streetAddress], .address, .location-text, address")
    if addr_el:
        data["address_full"] = addr_el.get_text(", ", strip=True)
        parts = [p.strip() for p in data["address_full"].split(",")]
        data["address_street"] = parts[0] if parts else ""
        data["address_city"]   = parts[-1] if len(parts) > 1 else ""
    else:
        # Regex for typical Greek address format: "Οδός Αριθμός, Πόλη"
        m = re.search(r"([Α-Ωα-ω\w]+\s+\d+[Α-Ω]?),\s*([Α-Ωα-ω\s]+)(?:\d{3}\s?\d{2})?", text)
        if m:
            data["address_street"] = m.group(1).strip()
            data["address_city"]   = m.group(2).strip()

    # Website
    for a in soup.select("a[href^='http']"):
        href = a.get("href", "")
        if href and BASE not in href and "facebook" not in href and "instagram" not in href:
            data["website"] = href
            break

    # Social links
    socials = {}
    for a in soup.select("a[href*='instagram.com'], a[href*='facebook.com'], a[href*='tiktok.com']"):
        href = a.get("href", "")
        for platform in ("instagram", "facebook", "tiktok"):
            if platform in href and platform not in socials:
                socials[platform] = href
    data["socials"] = socials

    # Primary photo (WordPress featured image)
    img = soup.select_one(".wp-post-image, .featured-image img, article img")
    if img:
        data["photo_url"] = img.get("src") or img.get("data-src")

    # Service categories from tags/categories on the post
    cats = []
    for a in soup.select(".cat-links a, .tags-links a, .entry-categories a, .business-categories a"):
        cats.append(a.get_text(strip=True))
    data["categories"] = cats

    return data


def save_listing(session, data: dict) -> Salon | None:
    name  = data.get("name", "")
    phone = data.get("phone_primary")

    existing = find_duplicate(session, name, phone, None, None)
    if existing:
        if not existing.description and data.get("description"):
            existing.description = data["description"]
        logger.debug("Duplicate: %s", name)
        sections = ["contact"] + (["photos"] if data.get("photo_url") else [])
        stamp(existing, source="beauty_project", sections=sections)
        return existing

    salon = Salon(
        name            = name,
        description     = data.get("description"),
        address_street  = data.get("address_street"),
        address_city    = data.get("address_city"),
        address_full    = data.get("address_full"),
        phone_primary   = phone,
        phone_secondary = data.get("phone_secondary"),
        website         = data.get("website"),
        is_active       = True,
    )
    session.add(salon)
    session.flush()

    if data.get("photo_url"):
        session.add(Photo(
            salon_id   = salon.id,
            url        = data["photo_url"],
            is_primary = True,
            source     = "beauty_project",
        ))

    for platform, url in data.get("socials", {}).items():
        session.add(SocialLink(salon_id=salon.id, platform=platform, url=url))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "beauty_project",
        source_url      = data.get("source_url"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = data,
    ))
    sections = ["contact"] + (["photos"] if data.get("photo_url") else [])
    stamp(salon, source="beauty_project", sections=sections)
    return salon


def run():
    session = get_session()
    total   = 0

    try:
        for page_num in range(1, MAX_PAGES + 1):
            logger.info("thebeautyproject.gr — page %d", page_num)
            try:
                soup = get_listing_page(page_num)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.info("  Page %d: 404 — end of listings", page_num)
                    break
                logger.error("  HTTP error on page %d: %s", page_num, e)
                break
            except Exception as e:
                logger.error("  Error on page %d: %s", page_num, e)
                break

            if not page_has_content(soup):
                logger.info("  No content on page %d — stopping", page_num)
                break

            detail_urls = extract_detail_urls(soup)
            logger.info("  Found %d listings on page %d", len(detail_urls), page_num)

            for url in detail_urls:
                try:
                    detail_soup = fetch(url)
                    data = parse_detail(detail_soup, url)
                    if data and data.get("name"):
                        salon = save_listing(session, data)
                        if salon:
                            total += 1
                            logger.info("  + %s (%s)", salon.name, salon.address_city or "—")
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error("  Error on %s: %s", url, e)
                time.sleep(1.5)

            time.sleep(2)

        logger.info("TheBeautyProject spider done — %d salons saved/updated", total)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
