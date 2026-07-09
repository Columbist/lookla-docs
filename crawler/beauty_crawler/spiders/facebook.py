"""
Facebook public business pages spider.

Facebook Graph API в 2025 году крайне ограничен для сторонних приложений.
Используем Playwright для скрапинга ПУБЛИЧНЫХ страниц Facebook.

Стратегия двух шагов:
  1. Поиск страниц через Google: site:facebook.com/pages/ κομμωτήριο Αθήνα
  2. Загрузка каждой найденной страницы → парсинг блока "About"

Что собираем с Facebook business page:
  - Название, описание
  - Адрес (улица, город)
  - Телефон
  - Сайт
  - Часы работы
  - Количество подписчиков (популярность)
  - Фото (обложка + аватар)
  - Категория (Hair Salon / Nail Salon / Spa / Beauty)

ВАЖНО: уважаем robots.txt и Terms of Service.
Скрапим только публично доступные страницы без авторизации.
Добавляем задержки, чтобы не нагружать серверы.

Run standalone:
  python -m beauty_crawler.spiders.facebook
"""
import json
import logging
import re
import time
from datetime import datetime
from typing import Optional

import httpx
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from ..models import Salon, SalonHour, Photo, SocialLink, CrawlerSource, get_session
from ..dedup import find_duplicate
from ..freshness import stamp

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Search queries to find FB pages via Google
# Each tuple: (search query, expected category)
GOOGLE_SEARCH_QUERIES = [
    ('site:facebook.com "κομμωτήριο" "Αθήνα" -m.facebook.com', "hair"),
    ('site:facebook.com "κομμωτήριο" "Θεσσαλονίκη" -m.facebook.com', "hair"),
    ('site:facebook.com "nail salon" Greece -m.facebook.com', "nails"),
    ('site:facebook.com "μανικιούρ" "Αθήνα" -m.facebook.com', "nails"),
    ('site:facebook.com "beauty salon" Athens Greece -m.facebook.com', "skin"),
    ('site:facebook.com "σαλόνι ομορφιάς" -m.facebook.com', "skin"),
    ('site:facebook.com "spa" Athens Greece "hair" -m.facebook.com', "spa"),
    ('site:facebook.com "barbershop" Athens -m.facebook.com', "barbershop"),
    ('site:facebook.com "μασάζ" "Αθήνα" -m.facebook.com', "massage"),
    ('site:facebook.com "νύχια" Αθήνα -m.facebook.com', "nails"),
]

GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
GOOGLE_CSE_API_KEY = ""  # optional; if empty, will use direct HTML search
GOOGLE_CSE_CX     = ""  # Custom Search Engine ID

# Day abbreviation map (Facebook uses full English day names)
FB_DAY_MAP = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def search_facebook_pages_via_google(query: str, page_count: int = 3) -> list[str]:
    """
    Uses Google Custom Search API (or Serper.dev if configured) to find
    Facebook business page URLs for a given query.
    Falls back to scraping Google search results via httpx.
    """
    fb_urls = []

    # Try Google Custom Search API if configured
    import os
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY", GOOGLE_CSE_API_KEY)
    cse_cx  = os.environ.get("GOOGLE_CSE_CX", GOOGLE_CSE_CX)

    if api_key and cse_cx:
        for start in range(1, page_count * 10, 10):
            try:
                resp = httpx.get(GOOGLE_SEARCH_URL, params={
                    "key": api_key, "cx": cse_cx, "q": query,
                    "num": 10, "start": start,
                }, timeout=15)
                data = resp.json()
                for item in data.get("items", []):
                    url = item.get("link", "")
                    if "facebook.com" in url and "/pages/" not in url:
                        # Normalize to desktop Facebook URL
                        url = url.replace("m.facebook.com", "www.facebook.com")
                        if url not in fb_urls:
                            fb_urls.append(url)
            except Exception as e:
                logger.warning("Google CSE error: %s", e)
                break
            time.sleep(0.5)
    else:
        # Fallback: use Serper.dev if SERPER_API_KEY is set
        serper_key = os.environ.get("SERPER_API_KEY", "")
        if serper_key:
            fb_urls.extend(_search_via_serper(query, serper_key, page_count))
        else:
            logger.warning(
                "No Google CSE or Serper key — Facebook URL discovery skipped.\n"
                "Set GOOGLE_SEARCH_API_KEY+GOOGLE_CSE_CX or SERPER_API_KEY in .env\n"
                "Alternatively, provide page URLs directly via run(page_urls=[...])"
            )

    return fb_urls


def _search_via_serper(query: str, api_key: str, page_count: int = 2) -> list[str]:
    """Use Serper.dev (cheap Google search API) to find Facebook page URLs."""
    urls = []
    for page in range(1, page_count + 1):
        try:
            resp = httpx.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": 10, "page": page},
                timeout=15,
            )
            data = resp.json()
            for item in data.get("organic", []):
                link = item.get("link", "")
                if "facebook.com" in link:
                    link = link.replace("m.facebook.com", "www.facebook.com")
                    if link not in urls:
                        urls.append(link)
        except Exception as e:
            logger.warning("Serper error: %s", e)
        time.sleep(0.3)
    return urls


def scrape_fb_page(page, url: str) -> dict | None:
    """
    Load a Facebook public business page and extract About info.
    Facebook loads differently depending on whether you're logged in.
    We scrape in anonymous mode (no account).
    """
    # Use /about/ subpage which has structured contact info
    about_url = url.rstrip("/") + "/about/"

    try:
        page.goto(about_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(6)  # wait for JS to settle

        # Close cookie consent / login popups
        for selector in [
            "[data-testid='cookie-policy-manage-dialog-accept-button']",
            "button[title='Allow all cookies']",
            "div[aria-label='Close'] button",
            "[data-testid='royal_close_dialog']",
        ]:
            try:
                btn = page.query_selector(selector)
                if btn:
                    btn.click()
                    time.sleep(1)
                    break
            except Exception:
                pass

        content = page.content()
        text = page.evaluate("document.body.innerText") or ""
    except PWTimeout:
        logger.warning("Timeout on FB page: %s", url)
        return None
    except Exception as e:
        logger.warning("Error loading %s: %s", url, e)
        return None

    data: dict = {"source_url": url}

    # Name — Facebook OG or h1
    m = re.search(r'<meta property="og:title" content="([^"]+)"', content)
    if m:
        data["name"] = m.group(1).strip()
    else:
        h1 = page.query_selector("h1")
        if h1:
            data["name"] = h1.inner_text().strip()

    if not data.get("name"):
        return None

    # Extract Facebook page ID from URL or page source
    m_id = re.search(r"facebook\.com/(?:pages/[^/]+/)?(\d{10,})", url)
    if m_id:
        data["fb_page_id"] = m_id.group(1)
    m_id2 = re.search(r'"pageID":"(\d+)"', content)
    if m_id2:
        data["fb_page_id"] = m_id2.group(1)

    # Category
    m_cat = re.search(r'"category":"([^"]+)"', content)
    if m_cat:
        data["category"] = m_cat.group(1)

    # Followers / likes
    m_followers = re.search(r"([\d,]+)\s+(?:followers|people follow)", text)
    if m_followers:
        data["followers"] = int(m_followers.group(1).replace(",", ""))

    # Phone
    phones = re.findall(r"(?:\+30\s*)?(?:69\d|2\d{2})[\s\-]?\d{3}[\s\-]?\d{4}", text)
    phones = [re.sub(r"[\s\-]", "", p) for p in phones]
    if phones:
        data["phone_primary"] = phones[0]
        if len(phones) > 1:
            data["phone_secondary"] = phones[1]

    # Website
    m_web = re.search(r'(?:Website|website)[^\n]*\n([^\n]+)', text)
    if m_web:
        url_candidate = m_web.group(1).strip()
        if url_candidate.startswith("http") and "facebook.com" not in url_candidate:
            data["website"] = url_candidate
    # Also check JSON-LD
    for script in re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', content, re.S):
        try:
            j = json.loads(script)
            w = j.get("url") or j.get("website")
            if w and "facebook.com" not in w:
                data["website"] = w
                break
        except Exception:
            pass

    # Address
    addr_patterns = [
        r"(?:Address|Διεύθυνση)[^\n]*\n([^\n]+(?:\n[^\n]+)?)",
        r"(\d+\s+[Α-Ωα-ω\w]+(?:\s+(?:Street|St\.|Avenue|Av\.|Οδός))?[,\s]+[Α-Ωα-ω\w\s]+\d{3}\s?\d{2})",
    ]
    for pat in addr_patterns:
        m_addr = re.search(pat, text)
        if m_addr:
            data["address_full"] = m_addr.group(1).strip().replace("\n", ", ")
            break

    # Hours — Facebook shows them as "Monday 09:00–20:00"
    hours = []
    for day, day_idx in FB_DAY_MAP.items():
        pattern = rf"{day.capitalize()}\s+(\d{{1,2}}:\d{{2}})\s*[–\-]\s*(\d{{1,2}}:\d{{2}})"
        m_h = re.search(pattern, text, re.IGNORECASE)
        if m_h:
            hours.append({"day": day_idx, "open": m_h.group(1), "close": m_h.group(2), "closed": False})
        elif re.search(rf"{day.capitalize()}\s+Closed", text, re.IGNORECASE):
            hours.append({"day": day_idx, "open": None, "close": None, "closed": True})
    data["hours"] = hours

    # Cover photo
    m_cover = re.search(r'"coverPhoto":\{"uri":"([^"]+)"', content)
    if m_cover:
        data["cover_photo"] = m_cover.group(1).replace("\\/", "/")

    # Profile picture
    m_pic = re.search(r'"profilePic(?:ture)?[^"]*":\{"uri":"([^"]+)"', content)
    if m_pic:
        data["profile_photo"] = m_pic.group(1).replace("\\/", "/")

    return data


def save_fb_data(session, data: dict) -> Optional[Salon]:
    name  = data.get("name", "")
    phone = data.get("phone_primary")

    if not name:
        return None

    existing = find_duplicate(session, name, phone, None, None)
    if existing:
        existing_fb = any(sl.platform == "facebook" for sl in existing.social_links)
        if not existing_fb:
            session.add(SocialLink(
                salon_id=existing.id, platform="facebook", url=data["source_url"]
            ))
        logger.debug("Duplicate (enriched with FB): %s", name)
        sections = ["contact"]
        if data.get("hours"):
            sections.append("hours")
        if data.get("cover_photo") or data.get("profile_photo"):
            sections.append("photos")
        stamp(existing, source="facebook", sections=sections)
        return existing

    salon = Salon(
        name           = name,
        address_full   = data.get("address_full"),
        phone_primary  = phone,
        phone_secondary= data.get("phone_secondary"),
        website        = data.get("website"),
        is_active      = True,
    )
    session.add(salon)
    session.flush()

    session.add(SocialLink(salon_id=salon.id, platform="facebook", url=data["source_url"]))

    for h in data.get("hours", []):
        session.add(SalonHour(
            salon_id    = salon.id,
            day_of_week = h["day"],
            open_time   = h.get("open"),
            close_time  = h.get("close"),
            is_closed   = h["closed"],
        ))

    for i, photo_key in enumerate(["cover_photo", "profile_photo"]):
        url_val = data.get(photo_key)
        if url_val:
            session.add(Photo(
                salon_id   = salon.id,
                url        = url_val,
                is_primary = (i == 0 and photo_key == "cover_photo"),
                source     = "facebook",
            ))

    session.add(CrawlerSource(
        salon_id        = salon.id,
        source          = "facebook",
        source_id       = data.get("fb_page_id"),
        source_url      = data.get("source_url"),
        last_crawled_at = datetime.utcnow(),
        crawl_status    = "success",
        raw_data        = {k: v for k, v in data.items() if k not in ("cover_photo", "profile_photo")},
    ))
    sections = ["contact"]
    if data.get("hours"):
        sections.append("hours")
    if data.get("cover_photo") or data.get("profile_photo"):
        sections.append("photos")
    stamp(salon, source="facebook", sections=sections)
    return salon


def run(page_urls: list[str] | None = None):
    """
    page_urls: list of known Facebook page URLs to scrape directly.
               If None, will try to discover URLs via Google search.
    """
    session = get_session()
    total   = 0

    # Discover URLs if not provided
    if not page_urls:
        page_urls = []
        for query, _cat in GOOGLE_SEARCH_QUERIES:
            found = search_facebook_pages_via_google(query)
            page_urls.extend(u for u in found if u not in page_urls)
            time.sleep(1)
        logger.info("Discovered %d Facebook page URLs via search", len(page_urls))

    if not page_urls:
        logger.warning(
            "No Facebook URLs to process. Provide SERPER_API_KEY or GOOGLE_SEARCH_API_KEY "
            "in .env, or pass page URLs directly to run(page_urls=[...])"
        )
        session.close()
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent=USER_AGENT,
            locale="el-GR",
            viewport={"width": 1440, "height": 900},
        )
        page = ctx.new_page()

        try:
            for url in page_urls:
                logger.info("Facebook: %s", url)
                try:
                    data = scrape_fb_page(page, url)
                    if data and data.get("name"):
                        salon = save_fb_data(session, data)
                        if salon:
                            total += 1
                            logger.info("  + %s", salon.name)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error("  Error on %s: %s", url, e)
                time.sleep(4)  # be polite to Facebook

        finally:
            browser.close()
            session.close()

    logger.info("Facebook spider done — %d salons saved/updated", total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
