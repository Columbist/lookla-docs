"""
Vrisko.gr spider — Greek business directory.

vrisko.gr lists businesses with name, address, phone, hours, category.
No JS rendering needed for listing pages.

Run standalone:
  python -m beauty_crawler.spiders.vrisko
"""
import logging
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlencode

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Salon, SalonHour, CrawlerSource, SocialLink, get_session
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

BASE_URL   = "https://www.vrisko.gr"
SEARCH_URL = "https://www.vrisko.gr/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "el-GR,el;q=0.9,en-US;q=0.8",
}

# Search terms → (Greek query, category slug)
SEARCHES = [
    ("κομμωτήριο", "hair"),
    ("μανικιούρ πεντικιούρ", "nails"),
    ("σαλόνι ομορφιάς", "skin"),
    ("αισθητική", "skin"),
    ("μασάζ spa", "massage"),
    ("barbershop κούρεμα", "barbershop"),
    ("τατουάζ piercing", "tattoo_piercing"),
]

CITIES = [
    "Αθήνα", "Θεσσαλονίκη", "Πάτρα", "Ηράκλειο", "Λάρισα",
    "Βόλος", "Ιωάννινα", "Χανιά", "Ρόδος", "Καβάλα",
    "Πειραιάς", "Γλυφάδα", "Κηφισιά", "Μαρούσι",
]

DAY_MAP_EL = {
    "δευτερα": 0, "τριτη": 1, "τεταρτη": 2, "πεμπτη": 3,
    "παρασκευη": 4, "σαββατο": 5, "κυριακη": 6,
    # abbreviations
    "δευ": 0, "τρι": 1, "τετ": 2, "πεμ": 3, "παρ": 4, "σαβ": 5, "κυρ": 6,
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
def fetch(url: str, params: dict | None = None) -> BeautifulSoup:
    resp = httpx.get(url, params=params, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_listing_page(soup: BeautifulSoup) -> list[str]:
    """Return detail-page URLs from a vrisko search results page."""
    links = []
    for a in soup.select("a[href*='/business/'], a[href*='/listing/']"):
        href = a.get("href", "")
        if href:
            links.append(urljoin(BASE_URL, href))
    return list(dict.fromkeys(links))  # dedup while preserving order


def parse_detail(soup: BeautifulSoup, url: str) -> dict | None:
    data: dict = {"source_url": url}

    # Name
    name_el = soup.select_one("h1.business-name, h1.listing-title, [itemprop=name]")
    if not name_el:
        return None
    data["name"] = name_el.get_text(strip=True)

    # Address
    addr_el = soup.select_one("[itemprop=streetAddress], .address-text, .business-address")
    if addr_el:
        data["address_full"] = addr_el.get_text(strip=True)
        # Try to split street + city
        parts = [p.strip() for p in data["address_full"].split(",")]
        data["address_street"] = parts[0] if parts else ""
        data["address_city"]   = parts[-1] if len(parts) > 1 else ""

    # City from breadcrumb
    bc = soup.select(".breadcrumb a, nav.breadcrumb a")
    if bc:
        data["address_city"] = bc[-1].get_text(strip=True)

    # Phone
    phones = []
    for el in soup.select("[itemprop=telephone], .phone-number, a[href^='tel:']"):
        ph = el.get("href", "").replace("tel:", "") or el.get_text(strip=True)
        ph = re.sub(r"[^\d+]", "", ph)
        if ph:
            phones.append(ph)
    if phones:
        data["phone_primary"]   = phones[0]
        data["phone_secondary"] = phones[1] if len(phones) > 1 else None

    # Website
    web_el = soup.select_one("[itemprop=url] a, a.business-website")
    if web_el:
        data["website"] = web_el.get("href") or web_el.get_text(strip=True)

    # Rating
    rating_el = soup.select_one("[itemprop=ratingValue], .rating-value")
    if rating_el:
        try:
            data["rating_google"] = float(rating_el.get_text(strip=True).replace(",", "."))
        except ValueError:
            pass

    # Hours — vrisko typically shows "Δευ–Παρ: 09:00–20:00"
    hours = []
    hours_el = soup.select_one(".opening-hours, [itemprop=openingHours], .business-hours")
    if hours_el:
        text = hours_el.get_text(" ", strip=True)
        # e.g. "Δευ - Παρ 09:00 - 20:00"
        m = re.findall(
            r"(\w+)\s*[-–]\s*(\w+)\s+(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})",
            text, re.UNICODE,
        )
        for start_day, end_day, open_t, close_t in m:
            s = DAY_MAP_EL.get(start_day.lower()[:3])
            e = DAY_MAP_EL.get(end_day.lower()[:3])
            if s is not None and e is not None:
                for d in range(s, e + 1):
                    hours.append({"day": d, "open": open_t, "close": close_t, "closed": False})
    data["hours"] = hours

    # Social
    socials = {}
    for a in soup.select("a[href*='instagram.com'], a[href*='facebook.com'], a[href*='tiktok.com']"):
        href = a.get("href", "")
        for platform in ("instagram", "facebook", "tiktok"):
            if platform in href:
                socials[platform] = href
    data["socials"] = socials

    return data


def save_listing(session, data: dict) -> Salon | None:
    name  = data.get("name", "")
    phone = data.get("phone_primary")
    existing = find_duplicate(session, name, phone, None, None)
    if existing:
        logger.debug("Duplicate: %s", name)
        stamp(existing, source="vrisko",
              sections=["contact"] + (["hours"] if data.get("hours") else []))
        return existing

    salon = Salon(
        name           = name,
        address_street = data.get("address_street"),
        address_city   = data.get("address_city"),
        address_full   = data.get("address_full"),
        phone_primary  = phone,
        phone_secondary= data.get("phone_secondary"),
        website        = data.get("website"),
        rating_google  = data.get("rating_google"),
        is_active      = True,
    )
    session.add(salon)
    session.flush()

    for h in data.get("hours", []):
        session.add(SalonHour(
            salon_id    = salon.id,
            day_of_week = h["day"],
            open_time   = h["open"],
            close_time  = h["close"],
            is_closed   = h["closed"],
        ))

    for platform, url in data.get("socials", {}).items():
        session.add(SocialLink(salon_id=salon.id, platform=platform, url=url))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "vrisko",
        source_url      = data.get("source_url"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = data,
    ))
    sections = ["contact"] + (["hours"] if data.get("hours") else [])
    stamp(salon, source="vrisko", sections=sections)
    return salon


def run(cities: list[str] | None = None):
    cities  = cities or CITIES
    session = get_session()
    total   = 0

    try:
        for city in cities:
            for query, _cat in SEARCHES:
                page = 1
                while page <= 10:  # cap at 10 pages per query
                    logger.info("vrisko: '%s' in %s — page %d", query, city, page)
                    try:
                        soup = fetch(SEARCH_URL, params={"q": query, "where": city, "page": page})
                    except Exception as e:
                        logger.error("Fetch error: %s", e)
                        break

                    detail_urls = parse_listing_page(soup)
                    if not detail_urls:
                        break

                    for url in detail_urls:
                        try:
                            detail_soup = fetch(url)
                            data = parse_detail(detail_soup, url)
                            if data:
                                salon = save_listing(session, data)
                                if salon:
                                    total += 1
                                    logger.info("  + %s (%s)", salon.name, salon.address_city)
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            logger.error("  Error on %s: %s", url, e)
                        time.sleep(1.5)

                    # Check if there's a "next page" link
                    next_btn = soup.select_one("a.next-page, a[rel=next], .pagination .next a")
                    if not next_btn:
                        break
                    page += 1
                    time.sleep(2)

        logger.info("Vrisko spider done — %d salons saved/updated", total)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
