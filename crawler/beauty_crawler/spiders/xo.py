"""
XO.gr spider — Χρυσός Οδηγός (Greek Yellow Pages).

URL pattern: https://www.xo.gr/dir-az/B/Beauty-Salons-and-Diet-Centers/{City}/
Each listing page has: name, address, phone, category, sometimes hours & website.

Run standalone:
  python -m beauty_crawler.spiders.xo
"""
import logging
import re
import time
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import Salon, SalonHour, CrawlerSource, get_session
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

BASE = "https://www.xo.gr"

# XO.gr has beauty salons under "Beauty-Salons-and-Diet-Centers"
# URL: https://www.xo.gr/dir-az/B/Beauty-Salons-and-Diet-Centers/{City}/?page={N}
CATEGORY_PATH = "/dir-az/B/Beauty-Salons-and-Diet-Centers"

CITIES = [
    "Athens", "Thessaloniki", "Patras", "Heraklion", "Larissa",
    "Volos", "Ioannina", "Chania", "Rhodes", "Kavala",
    "Piraeus", "Glyfada", "Kifisia", "Marousi", "Kalamaria",
    "Peristeri", "Nikaia", "Kallithea", "Ilioupoli", "Cholargos",
    "Halandri", "Amarousion", "Nea-Smyrni", "Alimos", "Vari",
    "Kerkyra", "Mytilene", "Kos", "Zakynthos", "Rethymno",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DAY_MAP_EN = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
def fetch(url: str, params: dict | None = None) -> BeautifulSoup:
    resp = httpx.get(url, params=params, headers=HEADERS, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def listing_urls_from_page(soup: BeautifulSoup) -> list[str]:
    """Extract detail URLs from a category listing page."""
    urls = []
    # XO listing items are typically in .listing-item or similar containers
    for a in soup.select(
        "a.listing-title, a.business-link, h2.listing-name a, "
        ".result-item a[href*='/biz/'], .company-name a, "
        "a[href*='/detail/'], a[href*='/company/']"
    ):
        href = a.get("href", "")
        if href:
            full = urljoin(BASE, href)
            if full not in urls:
                urls.append(full)
    return urls


def has_next_page(soup: BeautifulSoup) -> bool:
    return bool(soup.select_one("a.next, a[rel=next], .pagination .next:not(.disabled)"))


def parse_detail(soup: BeautifulSoup, url: str) -> dict | None:
    data: dict = {"source_url": url}

    # Name
    name_el = soup.select_one(
        "h1.business-name, h1.listing-name, h1[itemprop=name], "
        ".company-name h1, h1.profile-name"
    )
    if not name_el:
        # fallback: og:title
        og = soup.select_one('meta[property="og:title"]')
        if og:
            data["name"] = og.get("content", "").split(" | ")[0].strip()
        else:
            return None
    else:
        data["name"] = name_el.get_text(strip=True)

    if not data.get("name"):
        return None

    # Address — XO uses schema.org microdata
    addr_el = soup.select_one("[itemprop=streetAddress], .address, .company-address")
    city_el = soup.select_one("[itemprop=addressLocality], .city")
    postal_el = soup.select_one("[itemprop=postalCode], .postal")

    data["address_street"] = addr_el.get_text(strip=True) if addr_el else ""
    data["address_city"]   = city_el.get_text(strip=True)  if city_el else ""
    data["address_postal"] = postal_el.get_text(strip=True) if postal_el else ""
    data["address_full"]   = ", ".join(filter(None, [
        data["address_street"], data["address_city"], data["address_postal"]
    ]))

    # Phone
    phones = []
    for el in soup.select("[itemprop=telephone], a[href^='tel:'], .phone-number, .tel"):
        ph = (el.get("href") or el.get_text()).replace("tel:", "")
        ph = re.sub(r"[^\d+]", "", ph)
        if ph and len(ph) >= 8:
            phones.append(ph)
    if phones:
        data["phone_primary"]   = phones[0]
        data["phone_secondary"] = phones[1] if len(phones) > 1 else None

    # Website
    web = soup.select_one("[itemprop=url] a, a.website-link, a.external-link")
    if web:
        data["website"] = web.get("href") or web.get_text(strip=True)

    # Rating
    rating_el = soup.select_one("[itemprop=ratingValue], .rating-value, .stars-value")
    if rating_el:
        try:
            data["rating_google"] = float(rating_el.get_text(strip=True).replace(",", "."))
        except ValueError:
            pass

    # Hours — XO schema.org format: "Mo-Fr 09:00-20:00"
    hours = []
    for oh in soup.select("[itemprop=openingHours], .opening-hours span, .hours-row"):
        text = oh.get("content") or oh.get_text(" ", strip=True)
        # e.g. "Mo-Fr 09:00-21:00" or "Mo,Tu,We 10:00-19:00"
        m = re.findall(r"([A-Za-z]{2,3})[\s,\-–]+([A-Za-z]{2,3})?\s+(\d{1,2}:\d{2})\s*[\-–]\s*(\d{1,2}:\d{2})", text)
        for match in m:
            start, end, open_t, close_t = match
            s = DAY_MAP_EN.get(start.lower())
            e = DAY_MAP_EN.get(end.lower()) if end else s
            if s is not None:
                for d in range(s, (e or s) + 1):
                    hours.append({"day": d, "open": open_t, "close": close_t, "closed": False})
    data["hours"] = hours

    # Geo coords from map embed
    lat = lng = None
    map_el = soup.select_one("iframe[src*='maps.google'], [data-lat], [data-lng]")
    if map_el:
        lat = map_el.get("data-lat")
        lng = map_el.get("data-lng")
    if not lat:
        m = re.search(r"@([\d.]+),([\d.]+)", soup.get_text())
        if m:
            lat, lng = m.group(1), m.group(2)
    if lat:
        try:
            data["lat"] = float(lat)
            data["lng"] = float(lng)
        except (TypeError, ValueError):
            pass

    return data


def save_listing(session, data: dict) -> Salon | None:
    name  = data.get("name", "")
    phone = data.get("phone_primary")
    lat   = data.get("lat")
    lng   = data.get("lng")

    existing = find_duplicate(session, name, phone, lat, lng)
    if existing:
        if phone and not existing.phone_primary:
            existing.phone_primary = phone
        logger.debug("Duplicate: %s", name)
        stamp(existing, source="xo",
              sections=["contact"] + (["hours"] if data.get("hours") else []))
        return existing

    salon = Salon(
        name            = name,
        address_street  = data.get("address_street"),
        address_city    = data.get("address_city"),
        address_postal  = data.get("address_postal"),
        address_full    = data.get("address_full"),
        lat             = lat,
        lng             = lng,
        phone_primary   = phone,
        phone_secondary = data.get("phone_secondary"),
        website         = data.get("website"),
        rating_google   = data.get("rating_google"),
        is_active       = True,
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

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "xo",
        source_url      = data.get("source_url"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = data,
    ))
    sections = ["contact"] + (["hours"] if data.get("hours") else [])
    stamp(salon, source="xo", sections=sections)
    return salon


def run(cities: list[str] | None = None):
    cities  = cities or CITIES
    session = get_session()
    total   = 0

    try:
        for city in cities:
            page_num = 1
            while page_num <= 20:
                url = f"{BASE}{CATEGORY_PATH}/{city}/"
                params = {"lang": "en"}
                if page_num > 1:
                    params["page"] = page_num
                logger.info("xo.gr: %s — page %d", city, page_num)

                try:
                    soup = fetch(url, params=params)
                except Exception as e:
                    logger.error("Fetch error (%s pg%d): %s", city, page_num, e)
                    break

                detail_urls = listing_urls_from_page(soup)
                if not detail_urls:
                    logger.info("  No listings found, stopping pagination")
                    break

                for durl in detail_urls:
                    try:
                        detail_soup = fetch(durl)
                        data = parse_detail(detail_soup, durl)
                        if data:
                            salon = save_listing(session, data)
                            if salon:
                                total += 1
                                logger.info("  + %s (%s)", salon.name, salon.address_city)
                        session.commit()
                    except Exception as e:
                        session.rollback()
                        logger.error("  Error on %s: %s", durl, e)
                    time.sleep(1.5)

                if not has_next_page(soup):
                    break
                page_num += 1
                time.sleep(2)

        logger.info("XO.gr spider done — %d salons saved/updated", total)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
