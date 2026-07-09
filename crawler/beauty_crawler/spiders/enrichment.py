"""
Enrichment spider — pulls data from linked booking platforms.

Sources:
  - Treatwell (treatwell.gr/katasthma/*) — services, reviews, hours, photos
  - Fresha (fresha.com/a/* or fresha.com/la/*) — services, staff, reviews, hours, photos, phone
  - ebarber (ebarber.gr/barbershops/*) — phone, geo

Run:
  docker exec beauty_crawler python -m beauty_crawler.spiders.enrichment
"""
import re
import json
import time
import logging
import hashlib
from datetime import datetime, date
from typing import Optional

import httpx
from sqlalchemy import text

from ..models import (
    Salon, SalonHour, Service, Photo, Review,
    CrawlerSource, get_session,
)

try:
    from ..models import Staff
except ImportError:
    Staff = None

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get(url: str, timeout: int = 20) -> Optional[str]:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=timeout, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        logger.warning("GET %s failed: %s", url, e)
    return None


def _iso_duration_to_min(s: str) -> Optional[int]:
    """PT30M → 30, PT1H15M → 75"""
    if not s:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", s)
    if not m:
        return None
    h = int(m.group(1) or 0)
    mins = int(m.group(2) or 0)
    return h * 60 + mins or None


def _ld_json(html: str) -> Optional[dict]:
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    )
    for b in blocks:
        try:
            return json.loads(b)
        except Exception:
            pass
    return None


# ─────────────────────── TREATWELL ───────────────────────────────────────────

def _parse_treatwell_url(website: str) -> Optional[str]:
    """Normalize widget.treatwell.gr → www.treatwell.gr"""
    m = re.search(r"treatwell\.gr/katasthma/([^/?#]+)", website)
    if m:
        return f"https://www.treatwell.gr/katasthma/{m.group(1)}/"
    return None


def scrape_treatwell(salon_id: int, url: str, session) -> dict:
    result = {"services": 0, "reviews": 0, "photos": 0, "hours_updated": False}
    html = _get(url)
    if not html:
        return result

    ld = _ld_json(html)
    if not ld:
        return result

    graph = ld.get("@graph", [])
    biz = next((i for i in graph if i.get("@type") == "HealthAndBeautyBusiness"), None)
    if not biz:
        return result

    # ── Rating ───────────────────────────────────────────────────────────────
    agg = biz.get("aggregateRating", {})
    if agg.get("ratingValue"):
        session.execute(text("""
            INSERT INTO crawler_sources (salon_id, source, source_id, source_url,
                crawl_status, raw_data, last_crawled_at)
            VALUES (:sid, 'treatwell_meta', :sid_str, :url,
                'ok', CAST(:raw AS jsonb), NOW())
            ON CONFLICT (source, source_id)
            DO UPDATE SET raw_data = CAST(:raw AS jsonb), last_crawled_at = NOW()
        """), {
            "sid": salon_id,
            "sid_str": str(salon_id),
            "url": url,
            "raw": json.dumps({
                "rating": float(agg["ratingValue"]),
                "review_count": int(agg.get("reviewCount", 0)),
            }),
        })

    # ── Hours ─────────────────────────────────────────────────────────────────
    day_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    raw_hours = biz.get("openingHoursSpecification", [])
    if raw_hours:
        for spec in raw_hours:
            days = spec.get("dayOfWeek", [])
            opens = spec.get("opens")
            closes = spec.get("closes")
            for day_name in days:
                dow = day_map.get(day_name)
                if dow is None:
                    continue
                session.execute(text("""
                    INSERT INTO salon_hours
                      (salon_id, day_of_week, open_time, close_time, is_closed)
                    VALUES (:sid, :dow, :open, :close, false)
                    ON CONFLICT (salon_id, day_of_week)
                    DO UPDATE SET open_time = :open, close_time = :close, is_closed = false
                """), {"sid": salon_id, "dow": dow, "open": opens, "close": closes})
        result["hours_updated"] = True

    # ── Services ──────────────────────────────────────────────────────────────
    catalog = biz.get("hasOfferCatalog", {}).get("itemListElement", [])
    for cat in catalog:
        cat_name = cat.get("name", "")
        for offer in cat.get("itemListElement", []):
            svc = offer.get("itemOffered", {})
            name = svc.get("name", "").strip()
            if not name:
                continue
            desc = svc.get("description", "")
            dur_raw = svc.get("additionalProperty", {}).get("value", "")
            dur = _iso_duration_to_min(dur_raw)
            price_from = offer.get("price") or offer.get("lowPrice")
            price_to = offer.get("highPrice") or price_from
            src_id = hashlib.md5(f"{salon_id}:{name}:{cat_name}".encode()).hexdigest()[:20]

            session.execute(text("""
                INSERT INTO services
                  (salon_id, name, description, duration_min,
                   price_from, price_to, currency, source, source_id, is_active)
                VALUES (:sid, :name, :desc, :dur,
                        :pf, :pt, 'EUR', 'treatwell', :src_id, true)
                ON CONFLICT DO NOTHING
            """), {
                "sid": salon_id, "name": name, "desc": desc or None,
                "dur": dur, "pf": price_from or None, "pt": price_to or None,
                "src_id": src_id,
            })
            result["services"] += 1

    # ── Reviews ───────────────────────────────────────────────────────────────
    for rev in biz.get("review", []):
        author = rev.get("author", {}).get("name", "")
        body = rev.get("reviewBody", "")
        rating = int(rev.get("reviewRating", {}).get("ratingValue", 0))
        pub = rev.get("datePublished", "")
        src_id = hashlib.md5(f"tw:{salon_id}:{author}:{pub}:{body[:30]}".encode()).hexdigest()[:32]

        session.execute(text("""
            INSERT INTO reviews
              (salon_id, source, source_id, author_name, rating, text, published_at)
            VALUES (:sid, 'treatwell', :src_id, :author, :rating, :text, :pub)
            ON CONFLICT (source, source_id) DO NOTHING
        """), {
            "sid": salon_id, "src_id": src_id,
            "author": author or None,
            "rating": rating if 1 <= rating <= 5 else None,
            "text": body or None,
            "pub": pub or None,
        })
        result["reviews"] += 1

    # ── Photos ────────────────────────────────────────────────────────────────
    for i, img_url in enumerate(biz.get("image", [])):
        src_id = hashlib.md5(img_url.encode()).hexdigest()[:32]
        session.execute(text("""
            INSERT INTO photos (salon_id, url, is_primary, source)
            VALUES (:sid, :url, false, 'treatwell')
            ON CONFLICT (url) DO NOTHING
        """), {"sid": salon_id, "url": img_url})
        result["photos"] += 1

    session.commit()
    return result


# ─────────────────────── FRESHA ──────────────────────────────────────────────

def scrape_fresha(salon_id: int, url: str, session) -> dict:
    result = {"services": 0, "reviews": 0, "photos": 0, "staff": 0}
    html = _get(url)
    if not html:
        return result

    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return result

    try:
        nd = json.loads(m.group(1))
        pp = nd["props"]["pageProps"]
        # /a/ pages: props.pageProps.data.location
        if "data" in pp and isinstance(pp["data"], dict) and "location" in pp["data"]:
            loc = pp["data"]["location"]
        elif "location" in pp:
            loc = pp["location"]
        elif "initialData" in pp:
            # /book-now/ booking pages embed data differently — try to extract location
            idata = pp["initialData"]
            loc = (
                idata.get("location")
                or idata.get("venue")
                or next(
                    (v for v in idata.values() if isinstance(v, dict) and "name" in v),
                    None,
                )
            )
            if not loc:
                logger.warning("Fresha initialData: no location at %s", url)
                return result
        else:
            logger.warning("Fresha unexpected structure at %s, keys: %s", url, list(pp.keys())[:5])
            return result
    except Exception as e:
        logger.warning("Fresha parse %s: %s", url, e)
        return result

    # ── Basic fields ──────────────────────────────────────────────────────────
    salon = session.get(Salon, salon_id)
    if salon:
        if not salon.description and loc.get("description"):
            salon.description = loc["description"].strip() or None
        if not salon.phone_primary and loc.get("contactNumber"):
            salon.phone_primary = re.sub(r"\s+", "", loc["contactNumber"])

    # ── Rating ────────────────────────────────────────────────────────────────
    if loc.get("rating"):
        session.execute(text("""
            INSERT INTO crawler_sources (salon_id, source, source_id, source_url,
                crawl_status, raw_data, last_crawled_at)
            VALUES (:sid, 'fresha_meta', :sid_str, :url,
                'ok', CAST(:raw AS jsonb), NOW())
            ON CONFLICT (source, source_id)
            DO UPDATE SET raw_data = CAST(:raw AS jsonb), last_crawled_at = NOW()
        """), {
            "sid": salon_id, "sid_str": str(salon_id), "url": url,
            "raw": json.dumps({
                "rating": loc["rating"],
                "review_count": loc.get("reviewsCount", 0),
            }),
        })

    # ── Hours ─────────────────────────────────────────────────────────────────
    day_map = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6,
    }
    wt = loc.get("workingTime", {})
    days = wt.get("days", []) if isinstance(wt, dict) else []
    if days:
        for day in days:
            dow = day_map.get(day.get("dayName"))
            if dow is None:
                continue
            if day.get("isClosed"):
                session.execute(text("""
                    INSERT INTO salon_hours (salon_id, day_of_week, is_closed)
                    VALUES (:sid, :dow, true)
                    ON CONFLICT (salon_id, day_of_week)
                    DO UPDATE SET is_closed = true
                """), {"sid": salon_id, "dow": dow})
            else:
                vals = day.get("values", [{}])
                v = vals[0] if vals else {}
                opens = v.get("from", "")
                closes = v.get("to", "")
                if opens and closes:
                    session.execute(text("""
                        INSERT INTO salon_hours
                          (salon_id, day_of_week, open_time, close_time, is_closed)
                        VALUES (:sid, :dow, :open, :close, false)
                        ON CONFLICT (salon_id, day_of_week)
                        DO UPDATE SET open_time = :open, close_time = :close, is_closed = false
                    """), {"sid": salon_id, "dow": dow, "open": opens, "close": closes})

    # ── Services ──────────────────────────────────────────────────────────────
    for cat in loc.get("services", []):
        cat_name = cat.get("name", "")
        for svc in cat.get("items", []):
            name = svc.get("name", "").strip()
            if not name:
                continue
            desc = svc.get("description", "")
            dur_str = svc.get("caption", "")
            dur = None
            dur_m = re.search(r"(\d+)\s*(?:min|λεπτ)", dur_str, re.IGNORECASE)
            if dur_m:
                dur = int(dur_m.group(1))
            else:
                # "1 hr 30 min" style
                h_m = re.search(r"(\d+)\s*hr", dur_str)
                m_m = re.search(r"(\d+)\s*min", dur_str)
                if h_m or m_m:
                    dur = int(h_m.group(1) if h_m else 0) * 60 + int(m_m.group(1) if m_m else 0)

            rp = svc.get("retailPrice", {})
            price = rp.get("value") if rp else None
            src_id = svc.get("id") or hashlib.md5(
                f"{salon_id}:{name}:{cat_name}".encode()
            ).hexdigest()[:20]

            session.execute(text("""
                INSERT INTO services
                  (salon_id, name, description, duration_min,
                   price_from, price_to, currency, source, source_id, is_active)
                VALUES (:sid, :name, :desc, :dur,
                        :price, :price, 'EUR', 'fresha', :src_id, true)
                ON CONFLICT DO NOTHING
            """), {
                "sid": salon_id, "name": name, "desc": desc or None,
                "dur": dur, "price": price, "src_id": str(src_id),
            })
            result["services"] += 1

    # ── Reviews ───────────────────────────────────────────────────────────────
    for edge in loc.get("reviews", {}).get("edges", []):
        rev = edge.get("node", {})
        author = rev.get("reviewer", {}).get("name") or rev.get("authorName", "")
        body = rev.get("reviewBody") or rev.get("comment", "")
        rating = rev.get("rating")
        pub = rev.get("createdAt", "")[:10] if rev.get("createdAt") else None
        src_id = rev.get("id") or hashlib.md5(
            f"fresha:{salon_id}:{author}:{pub}:{body[:30]}".encode()
        ).hexdigest()[:32]

        if rating and rating > 5:
            rating = round(rating / 2)

        session.execute(text("""
            INSERT INTO reviews
              (salon_id, source, source_id, author_name, rating, text, published_at)
            VALUES (:sid, 'fresha', :src_id, :author, :rating, :text, :pub)
            ON CONFLICT (source, source_id) DO NOTHING
        """), {
            "sid": salon_id, "src_id": str(src_id),
            "author": author or None,
            "rating": int(rating) if rating and 1 <= int(rating) <= 5 else None,
            "text": body or None,
            "pub": pub,
        })
        result["reviews"] += 1

    # ── Photos ────────────────────────────────────────────────────────────────
    images = (
        loc.get("galleryModalDesktopLargeImages", [])
        or loc.get("galleryModalDesktopSmallImages", [])
    )
    for img in images:
        img_url = img.get("url", "")
        if not img_url:
            continue
        caption = img.get("shortDescription") or img.get("longDescription")
        src_id = hashlib.md5(img_url.split("?")[0].encode()).hexdigest()[:32]
        session.execute(text("""
            INSERT INTO photos (salon_id, url, caption, is_primary, source)
            VALUES (:sid, :url, :cap, false, 'fresha')
            ON CONFLICT (url) DO NOTHING
        """), {"sid": salon_id, "url": img_url, "cap": caption})
        result["photos"] += 1

    # ── Staff ─────────────────────────────────────────────────────────────────
    if Staff is not None:
        for edge in loc.get("employeeProfiles", {}).get("edges", []):
            emp = edge.get("node", {})
            name = emp.get("name") or emp.get("displayName", "")
            if not name:
                continue
            role = emp.get("jobTitle") or emp.get("role", "")
            bio = emp.get("bio", "")
            avatar = emp.get("avatar", {})
            photo_url = avatar.get("url") if isinstance(avatar, dict) else None
            src_id = str(emp.get("id") or hashlib.md5(
                f"{salon_id}:{name}".encode()
            ).hexdigest()[:20])

            session.execute(text("""
                INSERT INTO staff
                  (salon_id, name, bio, role, photo_url, source, source_id, is_active)
                VALUES (:sid, :name, :bio, :role, :photo, 'fresha', :src_id, true)
                ON CONFLICT (source, source_id) DO NOTHING
            """), {
                "sid": salon_id, "name": name,
                "bio": bio or None, "role": role or None,
                "photo": photo_url, "src_id": src_id,
            })
            result["staff"] += 1

    session.commit()
    return result


# ─────────────────────── EBARBER ─────────────────────────────────────────────

def scrape_ebarber(salon_id: int, url: str, session) -> dict:
    result = {"phone_updated": False, "geo_updated": False}
    html = _get(url)
    if not html:
        return result

    ld = _ld_json(html)
    if not ld:
        return result

    biz = ld if isinstance(ld, dict) else None
    if not biz:
        return result

    salon = session.get(Salon, salon_id)
    if not salon:
        return result

    phone = biz.get("telephone", "")
    if phone and not salon.phone_primary:
        salon.phone_primary = re.sub(r"\s+", "", phone)
        result["phone_updated"] = True

    geo = biz.get("geo", {})
    if geo and not salon.lat:
        try:
            salon.lat = float(geo["latitude"])
            salon.lng = float(geo["longitude"])
            result["geo_updated"] = True
        except (ValueError, KeyError):
            pass

    session.commit()
    return result


# ─────────────────────── MAIN ────────────────────────────────────────────────

def run():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    with get_session() as session:
        # Load all salons with platform links
        rows = session.execute(text("""
            SELECT id, name, website
            FROM salons
            WHERE is_active = true
              AND website IS NOT NULL
              AND (
                website ILIKE '%treatwell.gr/katasthma/%'
                OR website ILIKE '%widget.treatwell.gr/katasthma/%'
                OR website ILIKE '%fresha.com/a/%'
                OR website ILIKE '%fresha.com/la/%'
                OR website ILIKE '%fresha.com/book-now/%'
                OR website ILIKE '%ebarber.gr/barbershops/%'
              )
            ORDER BY id
        """)).fetchall()

        logger.info("Enrichment targets: %d salons", len(rows))
        totals = {"treatwell": 0, "fresha": 0, "ebarber": 0}
        stats = {
            "services": 0, "reviews": 0, "photos": 0,
            "staff": 0, "phones": 0,
        }

        for row in rows:
            sid, name, website = row.id, row.name, row.website
            w = website.lower()

            try:
                if "treatwell.gr/katasthma/" in w or "widget.treatwell.gr/katasthma/" in w:
                    tw_url = _parse_treatwell_url(website)
                    if not tw_url:
                        continue
                    r = scrape_treatwell(sid, tw_url, session)
                    totals["treatwell"] += 1
                    stats["services"] += r["services"]
                    stats["reviews"] += r["reviews"]
                    stats["photos"] += r["photos"]
                    logger.info(
                        "[TW] %s → svc:%d rev:%d photos:%d",
                        name, r["services"], r["reviews"], r["photos"],
                    )

                elif "fresha.com" in w:
                    r = scrape_fresha(sid, website, session)
                    totals["fresha"] += 1
                    stats["services"] += r["services"]
                    stats["reviews"] += r["reviews"]
                    stats["photos"] += r["photos"]
                    stats["staff"] += r.get("staff", 0)
                    logger.info(
                        "[FS] %s → svc:%d rev:%d photos:%d staff:%d",
                        name, r["services"], r["reviews"], r["photos"], r.get("staff", 0),
                    )

                elif "ebarber.gr/barbershops/" in w:
                    r = scrape_ebarber(sid, website, session)
                    totals["ebarber"] += 1
                    if r["phone_updated"]:
                        stats["phones"] += 1
                    logger.info(
                        "[EB] %s → phone:%s geo:%s",
                        name, r["phone_updated"], r["geo_updated"],
                    )

            except Exception as e:
                logger.error("Error on salon %d (%s): %s", sid, name, e)
                session.rollback()

            time.sleep(0.5)

        logger.info(
            "Done. TW:%d FS:%d EB:%d | services:%d reviews:%d photos:%d staff:%d phones:%d",
            totals["treatwell"], totals["fresha"], totals["ebarber"],
            stats["services"], stats["reviews"], stats["photos"],
            stats["staff"], stats["phones"],
        )


if __name__ == "__main__":
    run()
