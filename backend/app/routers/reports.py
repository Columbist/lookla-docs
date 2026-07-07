from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.models.user import User

router = APIRouter(tags=["reports"])
limiter = Limiter(key_func=get_remote_address)

VALID_REASONS = {'closed', 'wrong_phone', 'wrong_address', 'wrong_hours', 'duplicate', 'inappropriate', 'other'}


class ReportIn(BaseModel):
    salon_id: Optional[int] = None
    professional_id: Optional[int] = None
    reason: str
    description: Optional[str] = None


@router.post("/api/reports", status_code=201)
@limiter.limit("3/minute;10/hour")
def create_report(
    request: Request,
    body: ReportIn,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    if body.reason not in VALID_REASONS:
        raise HTTPException(400, "Invalid reason")
    if not body.salon_id and not body.professional_id:
        raise HTTPException(400, "salon_id or professional_id required")

    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else None)
    reporter_user_id = user.id if user else None

    # Dedup: same reporter + same target + same reason within 24 hours
    existing = db.execute(text("""
        SELECT id FROM reports
        WHERE reason = :reason
          AND (salon_id = :salon_id OR professional_id = :pro_id)
          AND created_at > NOW() - INTERVAL '24 hours'
          AND (
            (:uid IS NOT NULL AND reporter_user_id = :uid)
            OR (:ip IS NOT NULL AND reporter_ip = :ip)
          )
        LIMIT 1
    """), {
        "reason": body.reason,
        "salon_id": body.salon_id,
        "pro_id": body.professional_id,
        "uid": reporter_user_id,
        "ip": ip,
    }).first()

    if existing:
        return {"status": "ok"}  # silent dedup — don't reveal we skipped it

    db.execute(text("""
        INSERT INTO reports (salon_id, professional_id, reporter_user_id, reporter_ip, reason, description)
        VALUES (:salon_id, :professional_id, :uid, :ip, :reason, :description)
    """), {
        "salon_id": body.salon_id,
        "professional_id": body.professional_id,
        "uid": reporter_user_id,
        "ip": ip,
        "reason": body.reason,
        "description": body.description,
    })
    db.commit()

    # Auto-flag salon if 3+ open reports of same type
    if body.salon_id:
        count = db.execute(text("""
            SELECT COUNT(*) FROM reports
            WHERE salon_id = :sid AND reason = :reason AND status = 'open'
        """), {"sid": body.salon_id, "reason": body.reason}).scalar()
        if count >= 3:
            db.execute(text("UPDATE salons SET needs_review = true WHERE id = :id"), {"id": body.salon_id})
            db.commit()

    return {"status": "ok"}
