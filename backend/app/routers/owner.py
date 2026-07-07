"""
Owner dashboard endpoints: claiming salons, editing profile, managing services.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.salon import Salon, Service, SalonHour, SocialLink
from app.services.email import send_email

router = APIRouter(prefix="/api/owner", tags=["owner"])


# ─── Claim ────────────────────────────────────────────────────────────────────

class ClaimIn(BaseModel):
    salon_id: int
    channel: str = "sms"    # sms | email

@router.post("/claim/request")
async def request_claim(body: ClaimIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    salon = db.query(Salon).filter(Salon.id == body.salon_id).first()
    if not salon:
        raise HTTPException(404, "Salon not found")

    existing = db.execute(text(
        "SELECT id FROM salon_owners WHERE salon_id = :sid"
    ), {"sid": body.salon_id}).first()
    if existing:
        raise HTTPException(409, "Salon already claimed")

    token = secrets.token_hex(3).upper()   # "A3F9C1" — 6 chars
    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    db.execute(text("""
        INSERT INTO claiming_tokens (user_id, salon_id, token, expires_at)
        VALUES (:uid, :sid, :token, :exp)
        ON CONFLICT (user_id, salon_id)
        DO UPDATE SET token = :token, expires_at = :exp, used_at = NULL
    """), {"uid": user.id, "sid": body.salon_id, "token": token, "exp": expires})
    db.commit()

    # Send verification code
    if body.channel == "email" and salon.email:
        await send_email(salon.email, "claim", lang="el", code=token)
    # SMS/WhatsApp would go here when API keys are available

    return {"status": "ok", "hint": f"Code sent to salon contact ({body.channel})"}


@router.post("/claim/verify")
def verify_claim(salon_id: int, token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ct = db.execute(text("""
        SELECT id FROM claiming_tokens
        WHERE user_id = :uid AND salon_id = :sid AND token = :token
          AND used_at IS NULL AND expires_at > NOW()
    """), {"uid": user.id, "sid": salon_id, "token": token.upper()}).first()

    if not ct:
        raise HTTPException(400, "Invalid or expired verification code")

    # Mark used
    db.execute(text("UPDATE claiming_tokens SET used_at = NOW() WHERE id = :id"), {"id": ct.id})
    # Link owner
    db.execute(text("""
        INSERT INTO salon_owners (user_id, salon_id) VALUES (:uid, :sid)
        ON CONFLICT DO NOTHING
    """), {"uid": user.id, "sid": salon_id})
    # Mark verified
    db.execute(text("UPDATE salons SET is_verified = true WHERE id = :id"), {"id": salon_id})
    # Update user role
    db.execute(text("UPDATE users SET role = 'salon_owner' WHERE id = :id AND role = 'user'"), {"id": user.id})
    db.commit()

    return {"status": "ok", "message": "Salon claimed successfully"}


# ─── My salons ────────────────────────────────────────────────────────────────

@router.get("/salons")
def my_salons(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT s.id, s.name, s.slug, s.address_city, s.is_verified, s.is_active
        FROM salons s JOIN salon_owners so ON s.id = so.salon_id
        WHERE so.user_id = :uid
    """), {"uid": user.id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/salons/{salon_id}")
def get_my_salon(salon_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    row = db.execute(text("""
        SELECT s.id, s.name, s.slug, s.address_city, s.address_street, s.address_number,
               s.phone_primary, s.phone_secondary, s.email, s.website,
               s.description_el, s.description_en, s.is_verified, s.is_active
        FROM salons s WHERE s.id = :id
    """), {"id": salon_id}).mappings().first()
    if not row:
        raise HTTPException(404)

    services = db.execute(text("""
        SELECT id, name, name_el, duration_min, price_from, price_to, currency
        FROM services WHERE salon_id = :id ORDER BY id
    """), {"id": salon_id}).mappings().all()

    hours = db.execute(text("""
        SELECT day_of_week, open_time, close_time, is_closed
        FROM salon_hours WHERE salon_id = :id ORDER BY day_of_week
    """), {"id": salon_id}).mappings().all()

    social = db.execute(text("""
        SELECT platform, url FROM social_links WHERE salon_id = :id
    """), {"id": salon_id}).mappings().all()

    return {**dict(row), "services": [dict(r) for r in services],
            "hours": [dict(r) for r in hours], "social_links": [dict(r) for r in social]}


# ─── Edit salon ───────────────────────────────────────────────────────────────

class SalonUpdateIn(BaseModel):
    name: Optional[str] = None
    description_el: Optional[str] = None
    description_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_uk: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None


@router.put("/salons/{salon_id}")
def update_salon(salon_id: int, body: SalonUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return {"status": "ok"}
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    db.execute(text(f"UPDATE salons SET {set_clause}, updated_at = NOW() WHERE id = :salon_id"),
               {**updates, "salon_id": salon_id})
    db.commit()
    return {"status": "ok"}


# ─── Services ─────────────────────────────────────────────────────────────────

class ServiceIn(BaseModel):
    name: str
    name_el: Optional[str] = None
    description: Optional[str] = None
    duration_min: Optional[int] = None
    price_from: Optional[float] = None
    price_to: Optional[float] = None
    currency: str = "EUR"
    category_id: Optional[int] = None


@router.post("/salons/{salon_id}/services", status_code=201)
def add_service(salon_id: int, body: ServiceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    svc = Service(salon_id=salon_id, **body.model_dump())
    db.add(svc)
    db.commit()
    return {"id": svc.id, "status": "ok"}


@router.put("/salons/{salon_id}/services/{service_id}")
def update_service(salon_id: int, service_id: int, body: ServiceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    svc = db.query(Service).filter(Service.id == service_id, Service.salon_id == salon_id).first()
    if not svc:
        raise HTTPException(404)
    for k, v in body.model_dump().items():
        if v is not None:
            setattr(svc, k, v)
    db.commit()
    return {"status": "ok"}


@router.delete("/salons/{salon_id}/services/{service_id}")
def delete_service(salon_id: int, service_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    db.execute(text("DELETE FROM services WHERE id = :id AND salon_id = :sid"), {"id": service_id, "sid": salon_id})
    db.commit()
    return {"status": "ok"}


# ─── Hours ────────────────────────────────────────────────────────────────────

class HourItem(BaseModel):
    day_of_week: int
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    is_closed: bool = False

class HoursIn(BaseModel):
    hours: list[HourItem]


@router.put("/salons/{salon_id}/hours")
def update_hours(salon_id: int, body: HoursIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    for h in body.hours:
        db.execute(text("""
            INSERT INTO salon_hours (salon_id, day_of_week, open_time, close_time, is_closed)
            VALUES (:sid, :dow, :open, :close, :closed)
            ON CONFLICT (salon_id, day_of_week)
            DO UPDATE SET open_time = :open, close_time = :close, is_closed = :closed
        """), {"sid": salon_id, "dow": h.day_of_week, "open": h.open_time,
               "close": h.close_time, "closed": h.is_closed})
    db.execute(text("UPDATE salons SET hours_verified_at = NOW() WHERE id = :id"), {"id": salon_id})
    db.commit()
    return {"status": "ok"}


# ─── Social links ─────────────────────────────────────────────────────────────

@router.put("/salons/{salon_id}/social-links")
def update_social(salon_id: int, links: list[dict], user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_ownership(user.id, salon_id, db)
    for link in links:
        platform = link.get("platform")
        url = link.get("url", "")
        if not platform:
            continue
        if url:
            db.execute(text("""
                INSERT INTO social_links (salon_id, platform, url)
                VALUES (:sid, :platform, :url)
                ON CONFLICT (salon_id, platform) DO UPDATE SET url = :url
            """), {"sid": salon_id, "platform": platform, "url": url})
        else:
            db.execute(text("DELETE FROM social_links WHERE salon_id = :sid AND platform = :p"),
                       {"sid": salon_id, "p": platform})
    db.commit()
    return {"status": "ok"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_ownership(user_id: int, salon_id: int, db: Session):
    row = db.execute(text(
        "SELECT 1 FROM salon_owners WHERE user_id = :uid AND salon_id = :sid"
    ), {"uid": user_id, "sid": salon_id}).first()
    if not row:
        raise HTTPException(403, "Not authorized for this salon")
