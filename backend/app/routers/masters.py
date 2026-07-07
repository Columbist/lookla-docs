"""
Professional (master) registration and self-management.
"""
import re
import unicodedata
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.professional import Professional, ProfessionalAvailability, ProfessionalSocialLink

router = APIRouter(prefix="/api/masters", tags=["masters"])

SLUG_RE = re.compile(r"[^a-z0-9]+")


def _make_slug(name: str, user_id: int) -> str:
    """Deterministic slug: <name>-<user_id>. Unique because user_id is unique per professional."""
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    base = SLUG_RE.sub("-", normalized.lower()).strip("-")[:55] or "master"
    return f"{base}-{user_id}"


class ProfessionalCreateIn(BaseModel):
    name: str
    specialty: Optional[str] = None
    bio: Optional[str] = None
    bio_el: Optional[str] = None
    phone: Optional[str] = None
    instagram: Optional[str] = None
    email: Optional[str] = None
    base_city: Optional[str] = None
    base_lat: Optional[float] = None
    base_lng: Optional[float] = None
    service_radius_km: int = 15
    does_home_visits: bool = True
    has_home_studio: bool = False
    price_level: Optional[int] = None


class AvailabilityIn(BaseModel):
    schedule: list[dict]   # [{day_of_week, start_time, end_time, is_available}]


class SocialIn(BaseModel):
    links: list[dict]   # [{platform, url}]


@router.post("/register", status_code=201)
def register_professional(body: ProfessionalCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Professional).filter(Professional.user_id == user.id).first()
    if existing:
        raise HTTPException(409, "You already have a professional profile")

    slug = _make_slug(body.name, user.id)
    pro = Professional(user_id=user.id, slug=slug, is_active=False, **body.model_dump())  # pending review
    db.add(pro)
    db.flush()

    db.execute(text("UPDATE users SET role = 'professional' WHERE id = :id AND role = 'user'"), {"id": user.id})
    db.commit()

    return {"id": pro.id, "slug": pro.slug, "status": "pending_review",
            "message": "Profile submitted for review. You will be notified when approved."}


@router.get("/me")
def get_my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pro = db.query(Professional).filter(Professional.user_id == user.id).first()
    if not pro:
        raise HTTPException(404, "No professional profile")
    return pro


@router.put("/me")
def update_my_profile(body: ProfessionalCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pro = db.query(Professional).filter(Professional.user_id == user.id).first()
    if not pro:
        raise HTTPException(404, "No professional profile")
    for k, v in body.model_dump().items():
        if v is not None:
            setattr(pro, k, v)
    db.commit()
    return {"status": "ok"}


@router.put("/me/availability")
def update_availability(body: AvailabilityIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pro = db.query(Professional).filter(Professional.user_id == user.id).first()
    if not pro:
        raise HTTPException(404)
    for slot in body.schedule:
        db.execute(text("""
            INSERT INTO professional_availability (professional_id, day_of_week, start_time, end_time, is_available)
            VALUES (:pid, :dow, :start, :end, :avail)
            ON CONFLICT (professional_id, day_of_week)
            DO UPDATE SET start_time = :start, end_time = :end, is_available = :avail
        """), {"pid": pro.id, "dow": slot["day_of_week"], "start": slot.get("start_time"),
               "end": slot.get("end_time"), "avail": slot.get("is_available", True)})
    db.commit()
    return {"status": "ok"}


@router.put("/me/social-links")
def update_social(body: SocialIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pro = db.query(Professional).filter(Professional.user_id == user.id).first()
    if not pro:
        raise HTTPException(404)
    for link in body.links:
        platform, url = link.get("platform"), link.get("url", "")
        if not platform:
            continue
        if url:
            db.execute(text("""
                INSERT INTO professional_social_links (professional_id, platform, url)
                VALUES (:pid, :p, :u)
                ON CONFLICT (professional_id, platform) DO UPDATE SET url = :u
            """), {"pid": pro.id, "p": platform, "u": url})
        else:
            db.execute(text("DELETE FROM professional_social_links WHERE professional_id = :pid AND platform = :p"),
                       {"pid": pro.id, "p": platform})
    db.commit()
    return {"status": "ok"}
