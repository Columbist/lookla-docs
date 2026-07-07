"""Lazy photo proxy: serves Google Places photos, migrates them to R2 in the background."""
import logging
from threading import Lock

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.salon import Photo
from app.services.r2 import r2_key_for_photo, upload_bytes

log = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/media", tags=["media"])
limiter = Limiter(key_func=get_remote_address)

# Per-process state (2 workers → each has its own copy, which is acceptable:
# worst case = 2 Google downloads per photo, both R2 uploads are idempotent)
_in_flight: set[int] = set()  # currently being migrated
_failed: set[int] = set()     # failed this process lifetime — don't retry until restart
_lock = Lock()

GOOGLE_HOST = "places.googleapis.com"

# Cache-Control for responses
_NO_CACHE = {"Cache-Control": "no-store, no-cache"}
_LONG_CACHE = {"Cache-Control": "public, max-age=31536000"}


def _migrate(photo_id: int, salon_id: int, google_url: str) -> None:
    """Download from Google, upload to R2, update DB. Runs in a background thread."""
    try:
        r = httpx.get(google_url, follow_redirects=True, timeout=30)
        r.raise_for_status()
        data = r.content
        if len(data) < 1000:
            log.warning("Photo %d: tiny response (%d bytes), marking failed", photo_id, len(data))
            with _lock:
                _failed.add(photo_id)
                _in_flight.discard(photo_id)
            return

        ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
        ext = "jpg" if "jpeg" in ct else ct.split("/")[-1]
        key = r2_key_for_photo(salon_id, photo_id, google_url, ext)
        cdn_url = upload_bytes(settings, data, key, ct)

        # Update DB in a short-lived connection
        from app.core.database import SessionLocal
        with SessionLocal() as db:
            db.query(Photo).filter(Photo.id == photo_id).update({"url": cdn_url})
            db.commit()

        log.info("Photo %d migrated → %s", photo_id, cdn_url)
        with _lock:
            _in_flight.discard(photo_id)

    except Exception as e:
        log.warning("Photo %d migration failed: %s — will not retry until restart", photo_id, e)
        # Keep in _in_flight, add to _failed → prevents retry storm if R2/Google is down
        with _lock:
            _failed.add(photo_id)
            _in_flight.discard(photo_id)


@router.get("/photo/{photo_id}")
@limiter.limit("30/minute;200/hour")
def proxy_photo(request: Request, photo_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    url = photo.url

    # Already on R2/CDN — shouldn't normally reach here since salons router returns CDN URL directly
    if GOOGLE_HOST not in url:
        return RedirectResponse(url, status_code=301, headers=_LONG_CACHE)

    # Previously failed this process lifetime — redirect to Google, no retry
    with _lock:
        already_failed = photo_id in _failed

    if already_failed:
        return RedirectResponse(url, status_code=302, headers=_NO_CACHE)

    # Schedule migration (once per photo_id per process)
    with _lock:
        if photo_id not in _in_flight:
            _in_flight.add(photo_id)
            background_tasks.add_task(_migrate, photo_id, photo.salon_id, url)

    # Immediate redirect to Google — no-cache so browser re-checks after migration
    return RedirectResponse(url, status_code=302, headers=_NO_CACHE)
