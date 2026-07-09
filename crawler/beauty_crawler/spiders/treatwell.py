"""
Treatwell.gr spider.

Treatwell is JS-heavy (React), so we use Playwright to render pages.
Collects salons with full service menus, pricing, staff, and reviews.

Run standalone:
  python -m beauty_crawler.spiders.treatwell
"""
import json
import logging
import re
import time
from datetime import datetime

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from ..models import (
    Salon, SalonHour, Service, Photo, Review, SocialLink,
    CrawlerSource, get_session,
)
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

BASE  = "https://www.treatwell.gr"
# Listing pages by category
LISTING_URLS = [
    f"{BASE}/place/?q=hair-salon",
    f"{BASE}/place/?q=nail-salon",
    f"{BASE}/place/?q=beauty-salon",
    f"{BASE}/place/?q=massage",
    f"{BASE}/place/?q=barbershop",
    f"{BASE}/place/?q=eyebrows-eyelashes",
    f"{BASE}/place/?q=spa",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def make_browser_context(p):
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        user_agent=USER_AGENT,
        locale="el-GR",
        viewport={"width": 1440, "height": 900},
    )
    return browser, ctx


def extract_next_data(page_text: str) -> dict:
    """Extract __NEXT_DATA__ JSON embedded in Treatwell pages."""
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page_text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def get_listing_urls(page, start_url: str) -> list[str]:
    """Collect salon detail URLs from a Treatwell listing page."""
    urls = []
    try:
        page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        # Grab all venue links
        links = page.query_selector_all("a[href*='/place/']")
        for link in links:
            href = link.get_attribute("href")
            if href and "/place/" in href and href not in urls:
                full = href if href.startswith("http") else BASE + href
                # Exclude listing pages (only detail pages have a trailing slug)
                if full.count("/") >= 5:
                    urls.append(full)
    except PWTimeout:
        logger.warning("Timeout on listing page: %s", start_url)
    return urls


def parse_salon_page(page, url: str) -> dict | None:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)
        content = page.content()
    except PWTimeout:
        logger.warning("Timeout: %s", url)
        return None

    next_data = extract_next_data(content)
    props = (
        next_data.get("props", {})
                 .get("pageProps", {})
                 .get("venue") or
        next_data.get("props", {})
                 .get("pageProps", {})
                 .get("initialData", {})
                 .get("venue")
    )

    if not props:
        # Fallback: parse visible DOM text
        return _parse_dom_fallback(page, url)

    return _parse_next_data(props, url)


def _parse_next_data(venue: dict, url: str) -> dict:
    data: dict = {"source_url": url}

    data["name"]         = venue.get("name", "")
    data["description"]  = venue.get("description")
    data["website"]      = venue.get("websiteUrl")
    data["phone_primary"] = venue.get("phoneNumber")
    data["rating"]       = venue.get("rating", {}).get("average")
    data["rating_count"] = venue.get("rating", {}).get("count", 0)

    # Address
    addr = venue.get("address", {})
    data["address_street"] = addr.get("street")
    data["address_city"]   = addr.get("city") or addr.get("district")
    data["address_postal"] = addr.get("postcode")
    data["address_full"]   = ", ".join(filter(None, [
        addr.get("street"), addr.get("city"), addr.get("postcode")
    ]))

    # Geo
    geo = venue.get("location", {})
    data["lat"] = geo.get("lat")
    data["lng"] = geo.get("lng")

    # Hours
    hours = []
    for oh in venue.get("openingHours", []):
        day_idx = oh.get("dayOfWeek", 1) - 1  # 1=Mon on Treatwell
        hours.append({
            "day":    day_idx,
            "open":   oh.get("open"),
            "close":  oh.get("close"),
            "closed": oh.get("closed", False),
        })
    data["hours"] = hours

    # Services
    services = []
    for menu in venue.get("menus", []):
        for group in menu.get("items", []):
            for svc in group.get("treatmentGroups", []) or [group]:
                for treatment in svc.get("treatments", [svc]):
                    name = treatment.get("name") or svc.get("name", "")
                    if name:
                        services.append({
                            "name":         name,
                            "duration_min": treatment.get("durationMinutes"),
                            "price_from":   treatment.get("priceFrom"),
                            "price_to":     treatment.get("priceTo"),
                            "source_id":    str(treatment.get("id", "")),
                        })
    data["services"] = services

    # Photos
    photos = []
    for ph in venue.get("photos", [])[:15]:
        url_val = ph.get("url") or ph.get("original")
        if url_val:
            photos.append(url_val)
    data["photo_urls"] = photos

    # Reviews
    reviews = []
    for rv in venue.get("reviews", {}).get("items", [])[:50]:
        reviews.append({
            "source_id":   str(rv.get("id", "")),
            "author":      rv.get("author", {}).get("displayName", ""),
            "rating":      rv.get("rating"),
            "text":        rv.get("feedback"),
            "date":        rv.get("date"),
        })
    data["reviews"]   = reviews
    data["treatwell_id"] = str(venue.get("id", ""))

    return data


def _parse_dom_fallback(page, url: str) -> dict:
    """Minimal DOM parsing when __NEXT_DATA__ is not available."""
    data: dict = {"source_url": url}
    try:
        data["name"] = page.query_selector("h1").inner_text().strip()
    except Exception:
        return {}
    return data


def save_treatwell(session, data: dict) -> Salon | None:
    name  = data.get("name", "")
    if not name:
        return None

    lat  = data.get("lat")
    lng  = data.get("lng")
    phone = data.get("phone_primary")
    existing = find_duplicate(session, name, phone, lat, lng)
    if existing:
        logger.debug("Duplicate: %s", name)
        sections = ["contact"]
        if data.get("hours"):
            sections.append("hours")
        if data.get("services"):
            sections.append("services")
        if data.get("photo_urls"):
            sections.append("photos")
        stamp(existing, source="treatwell", sections=sections)
        return existing

    salon = Salon(
        name           = name,
        description    = data.get("description"),
        address_street = data.get("address_street"),
        address_city   = data.get("address_city"),
        address_postal = data.get("address_postal"),
        address_full   = data.get("address_full"),
        lat            = lat,
        lng            = lng,
        phone_primary  = phone,
        website        = data.get("website"),
        rating_google  = data.get("rating"),
        rating_count   = data.get("rating_count", 0),
        is_active      = True,
    )
    session.add(salon)
    session.flush()

    for h in data.get("hours", []):
        session.add(SalonHour(
            salon_id    = salon.id,
            day_of_week = h["day"],
            open_time   = h.get("open"),
            close_time  = h.get("close"),
            is_closed   = h.get("closed", False),
        ))

    for svc in data.get("services", []):
        session.add(Service(
            salon_id     = salon.id,
            name         = svc["name"],
            duration_min = svc.get("duration_min"),
            price_from   = svc.get("price_from"),
            price_to     = svc.get("price_to"),
            currency     = "EUR",
            source       = "treatwell",
            source_id    = svc.get("source_id"),
        ))

    for i, url_val in enumerate(data.get("photo_urls", [])):
        from ..models import Photo
        session.add(Photo(
            salon_id   = salon.id,
            url        = url_val,
            is_primary = (i == 0),
            source     = "treatwell",
        ))

    for rv in data.get("reviews", []):
        session.add(Review(
            salon_id    = salon.id,
            source      = "treatwell",
            source_id   = f"tw_{data.get('treatwell_id','')}_{rv.get('source_id','')}",
            author_name = rv.get("author"),
            rating      = rv.get("rating"),
            text        = rv.get("text"),
            published_at = rv.get("date"),
        ))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "treatwell",
        source_id       = data.get("treatwell_id"),
        source_url      = data.get("source_url"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = data,
    ))

    sections = ["contact"]
    if data.get("hours"):
        sections.append("hours")
    if data.get("services"):
        sections.append("services")
    if data.get("photo_urls"):
        sections.append("photos")
    stamp(salon, source="treatwell", sections=sections)

    return salon


def run(listing_urls: list[str] | None = None):
    listing_urls = listing_urls or LISTING_URLS
    session = get_session()
    total   = 0

    with sync_playwright() as p:
        browser, ctx = make_browser_context(p)
        page = ctx.new_page()

        try:
            all_detail_urls: list[str] = []
            for lurl in listing_urls:
                logger.info("Treatwell listing: %s", lurl)
                # Paginate
                for pg in range(1, 20):
                    paginated = f"{lurl}&page={pg}" if "?" in lurl else f"{lurl}?page={pg}"
                    urls = get_listing_urls(page, paginated)
                    if not urls:
                        break
                    all_detail_urls.extend(u for u in urls if u not in all_detail_urls)
                    time.sleep(2)

            logger.info("Treatwell: %d detail pages to scrape", len(all_detail_urls))
            for url in all_detail_urls:
                try:
                    data = parse_salon_page(page, url)
                    if data and data.get("name"):
                        salon = save_treatwell(session, data)
                        if salon:
                            total += 1
                            logger.info("  + %s (%s)", salon.name, salon.address_city)
                        session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error("  Error on %s: %s", url, e)
                time.sleep(3)

        finally:
            browser.close()
            session.close()

    logger.info("Treatwell spider done — %d salons saved/updated", total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
