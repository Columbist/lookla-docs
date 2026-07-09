"""Celery app + task definitions for the beauty crawler."""
import logging
import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("beauty_crawler", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Athens",
    enable_utc=True,
    worker_redirect_stdouts_level="INFO",
)

# ─── Periodic schedule ────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Daily Telegram report at 09:00 Athens time
    "daily-telegram-report": {
        "task": "beauty_crawler.celery_app.send_daily_report",
        "schedule": crontab(hour=9, minute=0),
    },
    # Google Places: monthly refresh on active cells (~287 cells × $0.032 = ~$9)
    "google-places-monthly": {
        "task": "beauty_crawler.celery_app.run_google",
        "schedule": crontab(hour=2, minute=0, day_of_week=1, day_of_month="1-7"),  # first Mon of month
    },
    # Google Places: quarterly full scan on all 515 cells (catches new areas)
    "google-places-quarterly": {
        "task": "beauty_crawler.celery_app.run_google_full",
        "schedule": crontab(hour=2, minute=0, day_of_month=1, month_of_year="1,4,7,10"),
    },
    "foursquare-weekly": {
        "task": "beauty_crawler.celery_app.run_foursquare",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),   # Mon 03:00
    },
    # Week 2: Greek HTML directories (slower, need polite delays)
    "vrisko-weekly": {
        "task": "beauty_crawler.celery_app.run_vrisko",
        "schedule": crontab(hour=2, minute=0, day_of_week=2),   # Tue 02:00
    },
    "xo-weekly": {
        "task": "beauty_crawler.celery_app.run_xo",
        "schedule": crontab(hour=4, minute=0, day_of_week=2),   # Tue 04:00
    },
    "beautyproject-weekly": {
        "task": "beauty_crawler.celery_app.run_beauty_project",
        "schedule": crontab(hour=2, minute=0, day_of_week=3),   # Wed 02:00
    },
    # Week 3: JS-heavy sources
    "treatwell-weekly": {
        "task": "beauty_crawler.celery_app.run_treatwell",
        "schedule": crontab(hour=2, minute=0, day_of_week=4),   # Thu 02:00
    },
    "facebook-weekly": {
        "task": "beauty_crawler.celery_app.run_facebook",
        "schedule": crontab(hour=2, minute=0, day_of_week=5),   # Fri 02:00
    },
}


@app.task(name="beauty_crawler.celery_app.send_daily_report")
def send_daily_report():
    from .telegram_notify import send_daily_report as _send
    logging.basicConfig(level=logging.INFO)
    _send()


@app.task(name="beauty_crawler.celery_app.run_google", bind=True, max_retries=2)
def run_google(self):
    from .spiders.google_places import run, generate_active_grid
    logging.basicConfig(level=logging.INFO)
    try:
        run(grid_cells=generate_active_grid())  # ~287 cells, ~$9
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_google_full", bind=True, max_retries=2)
def run_google_full(self):
    from .spiders.google_places import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()  # full 515 cells, ~$16
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_vrisko", bind=True, max_retries=2)
def run_vrisko(self):
    from .spiders.vrisko import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_treatwell", bind=True, max_retries=2)
def run_treatwell(self):
    from .spiders.treatwell import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_xo", bind=True, max_retries=2)
def run_xo(self):
    from .spiders.xo import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_beauty_project", bind=True, max_retries=2)
def run_beauty_project(self):
    from .spiders.beauty_project import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_foursquare", bind=True, max_retries=2)
def run_foursquare(self):
    from .spiders.foursquare import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


@app.task(name="beauty_crawler.celery_app.run_facebook", bind=True, max_retries=2)
def run_facebook(self):
    from .spiders.facebook import run
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
