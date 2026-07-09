"""
Online booking: check slots, create appointment, manage bookings.
"""
from datetime import datetime, timedelta, date, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


class BookingIn(BaseModel):
    salon_id: Optional[int] = None
    professional_id: Optional[int] = None
    service_id: Optional[int] = None
    staff_id: Optional[int] = None
    starts_at: datetime
    duration_min: int = 60
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    notes: Optional[str] = None


@router.get("/slots")
def get_slots(
    date: str,   # YYYY-MM-DD
    salon_id: Optional[int] = None,
    professional_id: Optional[int] = None,
    service_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Return available time slots for a given date."""
    try:
        target = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Invalid date format, use YYYY-MM-DD")

    day_of_week = (target.weekday())  # 0=Mon

    # Get working hours
    if salon_id:
        hours = db.execute(text("""
            SELECT open_time, close_time, is_closed FROM salon_hours
            WHERE salon_id = :sid AND day_of_week = :dow
        """), {"sid": salon_id, "dow": day_of_week}).first()
    elif professional_id:
        hours = db.execute(text("""
            SELECT start_time AS open_time, end_time AS close_time,
                   NOT is_available AS is_closed
            FROM professional_availability
            WHERE professional_id = :pid AND day_of_week = :dow
        """), {"pid": professional_id, "dow": day_of_week}).first()
    else:
        raise HTTPException(400, "salon_id or professional_id required")

    if not hours or hours.is_closed:
        return []

    open_h = int(hours.open_time.split(":")[0]) if isinstance(hours.open_time, str) else hours.open_time.hour
    close_h = int(hours.close_time.split(":")[0]) if isinstance(hours.close_time, str) else hours.close_time.hour

    # Get duration from service
    duration = 60
    if service_id:
        svc = db.execute(text("SELECT duration_min FROM services WHERE id = :id"), {"id": service_id}).first()
        if svc and svc.duration_min:
            duration = svc.duration_min

    # Get existing appointments for this day
    booked = db.execute(text("""
        SELECT starts_at, ends_at FROM appointments
        WHERE (:salon_id IS NULL OR salon_id = :salon_id)
          AND (:pro_id IS NULL OR professional_id = :pro_id)
          AND (:staff_id IS NULL OR staff_id = :staff_id)
          AND DATE(starts_at) = :target_date
          AND status NOT IN ('cancelled')
    """), {"salon_id": salon_id, "pro_id": professional_id, "staff_id": staff_id,
           "target_date": target}).mappings().all()

    booked_ranges = [(r.starts_at, r.ends_at) for r in booked]

    # Generate slots every 30 min
    slots = []
    current = datetime.combine(target, datetime.min.time().replace(hour=open_h))
    end_of_day = datetime.combine(target, datetime.min.time().replace(hour=close_h))

    while current + timedelta(minutes=duration) <= end_of_day:
        slot_end = current + timedelta(minutes=duration)
        # Check overlap
        overlaps = any(s < slot_end and e > current for s, e in booked_ranges)
        if not overlaps and current > datetime.now():
            slots.append({"time": current.strftime("%H:%M"), "available": True})
        current += timedelta(minutes=30)

    return {"date": date, "duration_min": duration, "slots": slots}


@router.post("", status_code=201)
def create_booking(
    body: BookingIn,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    ends_at = body.starts_at + timedelta(minutes=body.duration_min)

    # Check slot still available (basic race condition guard)
    conflict = db.execute(text("""
        SELECT id FROM appointments
        WHERE (:salon_id IS NULL OR salon_id = :salon_id)
          AND (:pro_id IS NULL OR professional_id = :pro_id)
          AND status NOT IN ('cancelled')
          AND starts_at < :ends_at AND ends_at > :starts_at
    """), {"salon_id": body.salon_id, "pro_id": body.professional_id,
           "starts_at": body.starts_at, "ends_at": ends_at}).first()

    if conflict:
        raise HTTPException(409, "This time slot is no longer available")

    appt_id = db.execute(text("""
        INSERT INTO appointments
          (salon_id, professional_id, staff_id, client_user_id, service_id,
           client_name, client_phone, client_email, starts_at, ends_at,
           duration_min, notes, status, source)
        VALUES
          (:salon_id, :pro_id, :staff_id, :client_id, :service_id,
           :client_name, :client_phone, :client_email, :starts_at, :ends_at,
           :duration_min, :notes, 'pending', 'web')
        RETURNING id
    """), {
        "salon_id": body.salon_id, "pro_id": body.professional_id,
        "staff_id": body.staff_id, "client_id": user.id if user else None,
        "service_id": body.service_id,
        "client_name": body.client_name, "client_phone": body.client_phone,
        "client_email": body.client_email, "starts_at": body.starts_at,
        "ends_at": ends_at, "duration_min": body.duration_min, "notes": body.notes,
    }).scalar()
    db.commit()

    return {"id": appt_id, "status": "pending",
            "message": "Booking created. You will receive a confirmation."}


@router.get("/mine")
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT a.id, a.starts_at, a.ends_at, a.status, a.notes,
               s.name AS salon_name, s.address_city,
               p.name AS pro_name,
               svc.name AS service_name
        FROM appointments a
        LEFT JOIN salons s ON a.salon_id = s.id
        LEFT JOIN professionals p ON a.professional_id = p.id
        LEFT JOIN services svc ON a.service_id = svc.id
        WHERE a.client_user_id = :uid
        ORDER BY a.starts_at DESC
        LIMIT 50
    """), {"uid": user.id}).mappings().all()
    return [dict(r) for r in rows]


@router.delete("/{appt_id}")
def cancel_booking(appt_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    appt = db.execute(text(
        "SELECT id, client_user_id, starts_at FROM appointments WHERE id = :id"
    ), {"id": appt_id}).first()
    if not appt:
        raise HTTPException(404)
    if appt.client_user_id != user.id:
        raise HTTPException(403)
    # Allow cancellation up to 2h before
    if appt.starts_at and appt.starts_at.replace(tzinfo=None) < datetime.now() + timedelta(hours=2):
        raise HTTPException(400, "Cannot cancel less than 2 hours before appointment")

    db.execute(text("UPDATE appointments SET status = 'cancelled', updated_at = NOW() WHERE id = :id"),
               {"id": appt_id})
    db.commit()
    return {"status": "ok"}


@router.get("/owner")
def owner_bookings(
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner sees bookings for their salons."""
    where = "so.user_id = :uid"
    params: dict = {"uid": user.id}
    if status:
        where += " AND a.status = :status"
        params["status"] = status
    if from_date:
        where += " AND a.starts_at >= :from_date"
        params["from_date"] = from_date

    rows = db.execute(text(f"""
        SELECT a.id, a.starts_at, a.ends_at, a.status,
               a.client_name, a.client_phone, a.notes,
               s.name AS salon_name,
               svc.name AS service_name
        FROM appointments a
        JOIN salons s ON a.salon_id = s.id
        JOIN salon_owners so ON s.id = so.salon_id
        LEFT JOIN services svc ON a.service_id = svc.id
        WHERE {where}
        ORDER BY a.starts_at ASC
        LIMIT 100
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/{appt_id}/status")
def update_booking_status(
    appt_id: int,
    status: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if status not in ("confirmed", "cancelled", "completed", "no_show"):
        raise HTTPException(400, "Invalid status")
    # Verify ownership
    check = db.execute(text("""
        SELECT a.id FROM appointments a
        JOIN salon_owners so ON a.salon_id = so.salon_id
        WHERE a.id = :appt_id AND so.user_id = :uid
    """), {"appt_id": appt_id, "uid": user.id}).first()
    if not check:
        raise HTTPException(403)
    db.execute(text("UPDATE appointments SET status = :s, updated_at = NOW() WHERE id = :id"),
               {"s": status, "id": appt_id})
    db.commit()
    return {"status": "ok"}
