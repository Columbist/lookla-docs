"""
Google Places API (New) spider — geographic grid coverage.

Covers all of Greece using a hexagonal grid of overlapping search circles.
No city list needed — any salon in Greece will be found regardless of its
administrative boundaries or how obscure its location is.

Grid: 0.35° lat × 0.45° lng steps (~38km × 39km at 38°N), 25km radius circles.
Total cells covering Greece: ~150-200 land cells out of ~500 grid points.

Run standalone:
  python -m beauty_crawler.spiders.google_places
"""
import logging
import os
import re
import time
from datetime import datetime, time as dtime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from unidecode import unidecode

from sqlalchemy import text as _sql_text
from ..models import Salon, SalonHour, CrawlerSource, get_session
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
BASE_URL = "https://places.googleapis.com/v1"

# Greece geographic bounding box
GRID_LAT_MIN, GRID_LAT_MAX = 34.7, 41.9
GRID_LNG_MIN, GRID_LNG_MAX = 19.2, 30.0
# Step and radius: radius > step/√2 ensures no gaps between circles
GRID_LAT_STEP = 0.35   # ~38 km
GRID_LNG_STEP = 0.45   # ~39 km at 38°N
SEARCH_RADIUS_M = 28000  # 28 km — overlaps adjacent cells

# Google Places category types — used with searchNearby (no language dependency)
PLACE_TYPES = [
    "beauty_salon",
    "hair_salon",
    "nail_salon",
    "barber_shop",
    "spa",
]

SEARCH_FIELDS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress",
    "places.location", "places.businessStatus", "places.types",
    "places.nationalPhoneNumber", "places.internationalPhoneNumber",
    "places.rating", "places.userRatingCount",
])

DETAIL_FIELDS = ",".join([
    "id", "displayName", "formattedAddress", "location",
    "nationalPhoneNumber", "internationalPhoneNumber", "websiteUri",
    "rating", "userRatingCount", "priceLevel",
    "regularOpeningHours",
    "addressComponents", "businessStatus", "googleMapsUri",
])

PRICE_LEVEL_MAP = {
    "PRICE_LEVEL_FREE":           0,
    "PRICE_LEVEL_INEXPENSIVE":    1,
    "PRICE_LEVEL_MODERATE":       2,
    "PRICE_LEVEL_EXPENSIVE":      3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


def generate_greece_grid() -> list[tuple[float, float]]:
    """Full hexagonal grid — 515 cells covering all of Greece bounding box."""
    cells = []
    lat = GRID_LAT_MIN
    row = 0
    while lat <= GRID_LAT_MAX + 0.01:
        lng = GRID_LNG_MIN
        if row % 2:
            lng += GRID_LNG_STEP / 2
        while lng <= GRID_LNG_MAX + 0.01:
            cells.append((round(lat, 3), round(lng, 3)))
            lng += GRID_LNG_STEP
        lat += GRID_LAT_STEP
        row += 1
    return cells


def generate_active_grid() -> list[tuple[float, float]]:
    """
    Returns only grid cells known to contain Greek salons (from DB).
    Use for monthly updates — ~287 cells vs 515 full grid.
    Full grid scan (generate_greece_grid) should run quarterly to catch new areas.
    """
    from ..models import get_session
    from sqlalchemy import text

    session = get_session()
    try:
        rows = session.execute(text("""
            SELECT
                ROUND((FLOOR(lat / :lat_step) * :lat_step)::numeric, 3) as cell_lat,
                ROUND((FLOOR(lng / :lng_step) * :lng_step)::numeric, 3) as cell_lng
            FROM salons
            WHERE lat BETWEEN 34.5 AND 42.0
              AND lng BETWEEN 19.0 AND 29.7
              AND is_active = true
            GROUP BY 1, 2
            ORDER BY 1, 2
        """), {"lat_step": GRID_LAT_STEP, "lng_step": GRID_LNG_STEP}).fetchall()
        return [(float(r[0]), float(r[1])) for r in rows]
    finally:
        session.close()


def _headers(field_mask: str) -> dict:
    return {
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": field_mask,
        "Content-Type": "application/json",
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def search_nearby(lat: float, lng: float, place_types: list[str] = PLACE_TYPES, radius_m: int = SEARCH_RADIUS_M) -> dict:
    """
    Uses Places API Nearby Search — returns all places of given types within
    the circle. No text query means no language dependency: a barbershop called
    'Κουρείο Γιώργος' is found just as reliably as 'George's Hair Salon'.
    Max 20 results per call (API limit); dense cells handled by smaller grid step.
    """
    body = {
        "includedTypes": place_types,
        "maxResultCount": 20,
        "languageCode": "el",
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": float(radius_m),
            }
        },
    }
    resp = httpx.post(
        f"{BASE_URL}/places:searchNearby",
        headers=_headers(SEARCH_FIELDS),
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def get_details(place_id: str) -> dict:
    resp = httpx.get(
        f"{BASE_URL}/places/{place_id}",
        headers=_headers(DETAIL_FIELDS),
        params={"languageCode": "el"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()



def parse_hours(opening_hours: dict) -> list[dict]:
    hours = []
    if not opening_hours:
        return hours
    periods = opening_hours.get("periods", [])
    if periods and len(periods) == 1 and periods[0].get("open", {}).get("day") == 0:
        for d in range(7):
            hours.append({"day": d, "open": "00:00", "close": "23:59", "closed": False})
        return hours
    for period in periods:
        open_p  = period.get("open", {})
        close_p = period.get("close", {})
        day_idx = open_p.get("day")
        if day_idx is None:
            continue
        day_idx = (day_idx - 1) % 7  # API: 0=Sun → convert to 0=Mon
        oh = open_p.get("hour", 0)
        om = open_p.get("minute", 0)
        ch = close_p.get("hour", 23)
        cm = close_p.get("minute", 59)
        hours.append({
            "day":    day_idx,
            "open":   dtime(oh, om),
            "close":  dtime(ch, cm),
            "closed": False,
        })
    present = {h["day"] for h in hours}
    for d in range(7):
        if d not in present:
            hours.append({"day": d, "open": None, "close": None, "closed": True})
    return hours


def save_place(session, raw: dict) -> Salon | None:
    place_id = raw.get("id")
    if not place_id:
        return None

    # Skip non-Greek locations
    country = next(
        (c.get("shortText") for c in raw.get("addressComponents", []) if "country" in c.get("types", [])),
        None,
    )
    if country and country != "GR":
        logger.debug("Skipping non-Greece place: %s (%s)", raw.get("displayName", {}).get("text"), country)
        return None

    loc   = raw.get("location", {})
    lat   = loc.get("latitude")
    lng   = loc.get("longitude")
    name  = raw.get("displayName", {}).get("text", "")
    phone = raw.get("nationalPhoneNumber") or raw.get("internationalPhoneNumber")

    existing = find_duplicate(session, name, phone, lat, lng, google_place_id=place_id)
    if existing:
        logger.debug("Duplicate: %s (%s)", name, place_id)
        new_rating = raw.get("rating")
        if new_rating and existing.rating_google != new_rating:
            existing.rating_google = new_rating
            existing.rating_count  = raw.get("userRatingCount", existing.rating_count)
        sections = ["contact"]
        if raw.get("regularOpeningHours"):
            sections.append("hours")
        if raw.get("photos"):
            sections.append("photos")
        stamp(existing, source="google_places", sections=sections)
        return existing

    addr_street = addr_number = addr_city = addr_postal = addr_region = ""
    for comp in raw.get("addressComponents", []):
        types = comp.get("types", [])
        val   = comp.get("longText", "")
        if "route" in types:
            addr_street = val
        elif "street_number" in types:
            addr_number = val
        elif "locality" in types or "postal_town" in types:
            addr_city = val
        elif "postal_code" in types:
            addr_postal = val
        elif "administrative_area_level_3" in types:
            addr_region = val

    price_raw   = raw.get("priceLevel", "")
    price_level = PRICE_LEVEL_MAP.get(price_raw)

    salon = Salon(
        name            = name,
        address_street  = addr_street,
        address_number  = addr_number,
        address_city    = addr_city or (lambda p: p[-2].strip() if len(p) >= 2 else "")(raw.get("formattedAddress", "").split(",")),
        address_region  = addr_region,
        address_postal  = addr_postal,
        address_full    = raw.get("formattedAddress"),
        lat             = lat,
        lng             = lng,
        google_place_id = place_id,
        phone_primary   = phone,
        website         = raw.get("websiteUri"),
        rating_google   = raw.get("rating"),
        rating_count    = raw.get("userRatingCount", 0),
        price_level     = price_level,
        is_active       = raw.get("businessStatus") == "OPERATIONAL",
    )
    session.add(salon)
    session.flush()

    # Generate slug immediately after flush (id is now available)
    if not salon.slug:
        base = re.sub(r"[^a-z0-9]+", "-", unidecode(name).lower()).strip("-")
        salon.slug = f"{base}-{salon.id}" if base else str(salon.id)

    # Merge split shifts per day (e.g. 9-14 + 17-21) — DB allows only one row/day
    hours_by_day: dict[int, dict] = {}
    for h in parse_hours(raw.get("regularOpeningHours", {})):
        d = h["day"]
        if d not in hours_by_day:
            hours_by_day[d] = h
        else:
            # Keep earliest open, latest close
            if h["open"] and (not hours_by_day[d]["open"] or h["open"] < hours_by_day[d]["open"]):
                hours_by_day[d]["open"] = h["open"]
            if h["close"] and (not hours_by_day[d]["close"] or h["close"] > hours_by_day[d]["close"]):
                hours_by_day[d]["close"] = h["close"]
    for h in hours_by_day.values():
        session.add(SalonHour(
            salon_id    = salon.id,
            day_of_week = h["day"],
            open_time   = h["open"],
            close_time  = h["close"],
            is_closed   = h["closed"],
        ))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "google_places",
        source_id       = place_id,
        source_url      = raw.get("googleMapsUri"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = raw,
    ))

    sections = ["contact"]
    if raw.get("regularOpeningHours"):
        sections.append("hours")
    stamp(salon, source="google_places", sections=sections)

    return salon


def run(grid_cells: list[tuple[float, float]] | None = None):
    """
    Crawl beauty salons across Greece using Nearby Search with place type categories.
    One API call per grid cell (vs. 6 text queries before) — uses Google's own
    classification so language of the salon name is irrelevant.
    """
    if not API_KEY:
        logger.error("GOOGLE_PLACES_API_KEY not set — skipping Google Places spider")
        return

    cells   = grid_cells or generate_greece_grid()
    session = get_session()
    total   = 0

    logger.info("Google Places spider: %d grid cells, types=%s", len(cells), PLACE_TYPES)

    try:
        for i, (lat, lng) in enumerate(cells):
            logger.info("[%d/%d] searchNearby @ (%.3f, %.3f)", i + 1, len(cells), lat, lng)
            try:
                data = search_nearby(lat, lng)
            except Exception as e:
                logger.error("Search error @ %.3f,%.3f: %s", lat, lng, e)
                continue

            places = data.get("places", [])
            if not places:
                continue

            for result in places:
                place_id = result.get("id")
                if not place_id:
                    continue
                # Check DB before calling paid Place Details API
                exists = session.execute(
                    _sql_text("SELECT 1 FROM crawler_sources WHERE source='google_places' AND source_id=:pid LIMIT 1"),
                    {"pid": place_id}
                ).fetchone()
                if exists:
                    continue  # already in DB — skip paid API call
                try:
                    details = get_details(place_id)
                    salon = save_place(session, details)
                    if salon and salon.id:
                        total += 1
                        logger.info("  + %s (%s)", salon.name, salon.address_city)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error("  Error saving %s: %s", place_id, e)
                time.sleep(0.2)

            time.sleep(0.5)

        logger.info("Google Places spider done — %d salons saved/updated", total)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
