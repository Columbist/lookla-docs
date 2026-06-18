from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db

router = APIRouter(tags=["reports"])

VALID_REASONS = {'closed','wrong_phone','wrong_address','wrong_hours','duplicate','inappropriate','other'}

class ReportIn(BaseModel):
    salon_id: Optional[int] = None
    professional_id: Optional[int] = None
    reason: str
    description: Optional[str] = None

@router.post("/api/reports", status_code=201)
def create_report(body: ReportIn, request: Request, db: Session = Depends(get_db)):
    if body.reason not in VALID_REASONS:
        from fastapi import HTTPException
        raise HTTPException(400, "Invalid reason")

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)

    db.execute(text("""
        INSERT INTO reports (salon_id, professional_id, reporter_ip, reason, description)
        VALUES (:salon_id, :professional_id, :ip, :reason, :description)
    """), {
        "salon_id": body.salon_id,
        "professional_id": body.professional_id,
        "ip": ip,
        "reason": body.reason,
        "description": body.description,
    })
    db.commit()

    # Auto-flag salon if 3+ reports of same type
    if body.salon_id:
        count = db.execute(text("""
            SELECT COUNT(*) FROM reports
            WHERE salon_id = :sid AND reason = :reason AND status = 'open'
        """), {"sid": body.salon_id, "reason": body.reason}).scalar()
        if count >= 3:
            db.execute(text("UPDATE salons SET needs_review = true WHERE id = :id"), {"id": body.salon_id})
            db.commit()

    return {"status": "ok"}
