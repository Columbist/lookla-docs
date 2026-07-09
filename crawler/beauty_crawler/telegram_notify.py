"""Telegram notification helpers for beauty-gr crawler."""
import logging
import os
from datetime import datetime, timedelta

import httpx

from .models import get_session, Salon, Photo, Review, CrawlerSource

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send(text: str) -> bool:
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram credentials not set — skipping notification")
        return False
    try:
        resp = httpx.post(
            TG_URL,
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Telegram send error: %s", e)
        return False


def daily_report() -> str:
    session = get_session()
    try:
        now   = datetime.utcnow()
        since = now - timedelta(hours=24)

        total_salons  = session.query(Salon).count()
        new_salons    = session.query(Salon).filter(Salon.created_at >= since).count()
        total_photos  = session.query(Photo).count()
        total_reviews = session.query(Review).count()

        # Per-source last crawl + today's count
        sources = ["google_places", "vrisko", "treatwell", "xo", "beauty_project", "foursquare"]
        source_lines = []
        for src in sources:
            last = (
                session.query(CrawlerSource)
                .filter(CrawlerSource.source == src)
                .order_by(CrawlerSource.last_crawled_at.desc())
                .first()
            )
            new_today = (
                session.query(CrawlerSource)
                .filter(
                    CrawlerSource.source == src,
                    CrawlerSource.last_crawled_at >= since,
                    CrawlerSource.crawl_status == "success",
                )
                .count()
            )
            errors = (
                session.query(CrawlerSource)
                .filter(
                    CrawlerSource.source == src,
                    CrawlerSource.last_crawled_at >= since,
                    CrawlerSource.crawl_status == "error",
                )
                .count()
            )
            if last and last.last_crawled_at:
                ts = last.last_crawled_at.strftime("%d.%m %H:%M")
                status = f"+{new_today} за 24ч" + (f", {errors} ошиб." if errors else "")
                source_lines.append(f"  • {src}: {ts} UTC  {status}")
            else:
                source_lines.append(f"  • {src}: не запускался")

        sources_block = "\n".join(source_lines)

        report = (
            f"<b>Beauty-GR — ежедневный отчёт</b>\n"
            f"{now.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
            f"<b>База данных:</b>\n"
            f"  Салонов всего:  {total_salons:,}\n"
            f"  Новых за 24ч:   {new_salons:,}\n"
            f"  Фотографий:     {total_photos:,}\n"
            f"  Отзывов:        {total_reviews:,}\n\n"
            f"<b>Краулеры:</b>\n"
            f"{sources_block}"
        )
        return report
    finally:
        session.close()


def send_daily_report():
    try:
        report = daily_report()
        send(report)
        logger.info("Daily Telegram report sent")
    except Exception as e:
        logger.error("Failed to build/send daily report: %s", e)
        send(f"<b>Beauty-GR</b> — ошибка при формировании отчёта:\n<code>{e}</code>")
