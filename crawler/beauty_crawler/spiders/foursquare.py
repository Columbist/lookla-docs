"""
Foursquare Places API spider.

Free tier: 10,000 requests/month on Pro endpoints.
Covers 100M+ global POIs including Greek beauty salons.

Docs: https://docs.foursquare.com/developer/reference/place-search
Requires: FOURSQUARE_API_KEY in environment.

Run standalone:
  python -m beauty_crawler.spiders.foursquare
"""
import logging
import os
import re
import time
from datetime import datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from unidecode import unidecode

from ..models import Salon, SalonHour, Photo, CrawlerSource, get_session
from ..dedup import find_duplicate
from ..freshness import stamp
from sqlalchemy import text as _sql_text

logger = logging.getLogger(__name__)

API_KEY  = os.environ.get("FOURSQUARE_API_KEY", "")
SEARCH   = "https://api.foursquare.com/v3/places/search"
DETAILS  = "https://api.foursquare.com/v3/places/{fsq_id}"
PHOTOS   = "https://api.foursquare.com/v3/places/{fsq_id}/photos"
HOURS_EP = "https://api.foursquare.com/v3/places/{fsq_id}/hours"

# Foursquare category IDs for beauty/wellness
CATEGORIES = {
    "17000": "Beauty Salon",   # top-level Beauty
    "17001": "Barbershop",
    "17002": "Hair Salon",
    "17003": "Nail Salon",
    "17049": "Spa",
    "17050": "Massage",
    "17007": "Cosmetics Store",  # lower priority
}

# Greek cities with approximate coordinates for the search radius
CITY_COORDS = [
    ("Athens",       37.9838, 23.7275),
    ("Thessaloniki", 40.6401, 22.9444),
    ("Patras",       38.2466, 21.7346),
    ("Heraklion",    35.3387, 25.1442),
    ("Larissa",      39.6390, 22.4191),
    ("Volos",        39.3621, 22.9432),
    ("Ioannina",     39.6650, 20.8537),
    ("Chania",       35.5138, 24.0180),
    ("Rhodes",       36.4341, 28.2176),
    ("Kavala",       40.9395, 24.4019),
    ("Piraeus",      37.9475, 23.6430),
    ("Glyfada",      37.8781, 23.7524),
    ("Kifisia",      38.0736, 23.8083),
]

RADIUS = 5000  # metres


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _get(url: str, params: dict) -> dict:
    resp = httpx.get(
        url,
        params=params,
        headers={"Authorization": API_KEY, "Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def search_places(lat: float, lng: float, category_id: str,
                  cursor: str | None = None) -> dict:
    params = {
        "ll":         f"{lat},{lng}",
        "radius":     RADIUS,
        "categories": category_id,
        "fields":     "fsq_id,name,location,geocodes,tel,website,rating,hours,photos,social_media",
        "limit":      50,
        "sort":       "RELEVANCE",
    }
    if cursor:
        params["cursor"] = cursor
    return _get(SEARCH, params)


def get_hours(fsq_id: str) -> list[dict]:
    try:
        data = _get(HOURS_EP.format(fsq_id=fsq_id), {})
        return data.get("regular", [])
    except Exception:
        return []


def parse_hours(regular: list[dict]) -> list[dict]:
    """Convert Foursquare hours format to our internal format."""
    hours = []
    for entry in regular:
        day = entry.get("day")  # 1=Mon, 7=Sun (Foursquare)
        if day is None:
            continue
        day_idx = (day - 1) % 7  # convert to 0=Mon
        open_t  = entry.get("open",  "")   # "0900"
        close_t = entry.get("close", "")   # "2000"

        def fmt(t: str) -> str:
            return f"{t[:2]}:{t[2:]}" if len(t) == 4 else t

        hours.append({
            "day":    day_idx,
            "open":   fmt(open_t)  if open_t  else None,
            "close":  fmt(close_t) if close_t else None,
            "closed": entry.get("closed", False),
        })
    return hours


def save_place(session, raw: dict) -> Salon | None:
    fsq_id = raw.get("fsq_id")
    name   = raw.get("name", "")
    if not name:
        return None

    loc  = raw.get("location", {})
    geo  = raw.get("geocodes", {}).get("main", {})
    lat  = geo.get("latitude")
    lng  = geo.get("longitude")
    phone = raw.get("tel")

    # Skip paid hours API call if already in DB
    already = session.execute(
        _sql_text("SELECT 1 FROM crawler_sources WHERE source='foursquare' AND source_id=:fid LIMIT 1"),
        {"fid": fsq_id},
    ).fetchone()
    if already:
        return None

    existing = find_duplicate(session, name, phone, lat, lng)
    if existing:
        logger.debug("Duplicate: %s (%s)", name, fsq_id)
        sections = ["contact"] + (["hours"] if raw.get("hours") else []) + (["photos"] if raw.get("photos") else [])
        stamp(existing, source="foursquare", sections=sections)
        return existing

    addr_parts = [
        loc.get("address"),
        loc.get("locality") or loc.get("city"),
        loc.get("region"),
    ]
    salon = Salon(
        name           = name,
        address_street = loc.get("address"),
        address_city   = loc.get("locality") or loc.get("city"),
        address_region = loc.get("region"),
        address_postal = loc.get("postcode"),
        address_full   = ", ".join(p for p in addr_parts if p),
        lat            = lat,
        lng            = lng,
        phone_primary  = phone,
        website        = raw.get("website"),
        rating_google  = round(raw["rating"] / 2, 1) if raw.get("rating") else None,  # Foursquare 1-10 → 0.5-5.0
        is_active      = True,
    )
    session.add(salon)
    session.flush()

    if not salon.slug:
        base = re.sub(r"[^a-z0-9]+", "-", unidecode(name).lower()).strip("-")
        salon.slug = f"{base}-{salon.id}" if base else str(salon.id)

    # Hours (separate API call)
    for h in parse_hours(get_hours(fsq_id)):
        session.add(SalonHour(
            salon_id    = salon.id,
            day_of_week = h["day"],
            open_time   = h["open"],
            close_time  = h["close"],
            is_closed   = h["closed"],
        ))

    # Photos (Foursquare includes prefix/suffix pattern)
    for i, ph in enumerate(raw.get("photos", [])[:8]):
        prefix = ph.get("prefix", "")
        suffix = ph.get("suffix", "")
        if prefix and suffix:
            session.add(Photo(
                salon_id   = salon.id,
                url        = f"{prefix}800x600{suffix}",
                is_primary = (i == 0),
                source     = "foursquare",
                width      = 800,
                height     = 600,
            ))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "foursquare",
        source_id       = fsq_id,
        source_url      = f"https://foursquare.com/v/{fsq_id}",
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = raw,
    ))
    sections = ["contact"]
    if raw.get("hours"):
        sections.append("hours")
    if raw.get("photos"):
        sections.append("photos")
    stamp(salon, source="foursquare", sections=sections)
    return salon


def run(city_coords: list | None = None):
    if not API_KEY:
        logger.error("FOURSQUARE_API_KEY not set — skipping Foursquare spider")
        return

    city_coords = city_coords or CITY_COORDS
    session = get_session()
    total   = 0

    try:
        for city_name, lat, lng in city_coords:
            for cat_id, cat_name in CATEGORIES.items():
                logger.info("Foursquare: %s / %s in %s", cat_id, cat_name, city_name)
                cursor = None
                page   = 0

                while True:
                    page += 1
                    try:
                        data = search_places(lat, lng, cat_id, cursor)
                    except Exception as e:
                        logger.error("  Search error: %s", e)
                        break

                    results = data.get("results", [])
                    if not results:
                        break

                    for place in results:
                        try:
                            salon = save_place(session, place)
                            if salon:
                                total += 1
                                logger.info("  + %s (%s)", salon.name, salon.address_city)
                            session.commit()
                        except Exception as e:
                            session.rollback()
                            logger.error("  Error saving %s: %s", place.get("name"), e)
                        time.sleep(0.1)

                    # Foursquare pagination via cursor in Link header or context
                    context = data.get("context", {})
                    cursor  = context.get("next_cursor")
                    if not cursor or page >= 10:  # cap: 500 results per city/category
                        break
                    time.sleep(0.5)

        logger.info("Foursquare spider done — %d salons saved/updated", total)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
