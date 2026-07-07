"""
Admin panel API — requires role='admin'.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM salons WHERE is_active = true)  AS total_salons,
            (SELECT COUNT(*) FROM salons WHERE is_verified = true) AS verified_salons,
            (SELECT COUNT(*) FROM salons WHERE needs_review = true) AS needs_review,
            (SELECT COUNT(*) FROM professionals WHERE is_active = true) AS total_pros,
            (SELECT COUNT(*) FROM users) AS total_users,
            (SELECT COUNT(*) FROM appointments WHERE DATE(created_at) = CURRENT_DATE) AS bookings_today,
            (SELECT COUNT(*) FROM appointments) AS total_bookings,
            (SELECT COUNT(*) FROM reports WHERE status = 'open') AS open_reports,
            (SELECT COUNT(*) FROM moderation_queue WHERE status = 'pending') AS moderation_pending
    """)).mappings().first()
    return dict(row)


@router.get("/salons")
def list_salons(
    page: int = 1, limit: int = 20,
    needs_review: Optional[bool] = None,
    verified: Optional[bool] = None,
    q: Optional[str] = None,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    where = "1=1"
    params: dict = {"limit": limit, "offset": (page-1)*limit}
    if needs_review is not None:
        where += " AND needs_review = :nr"; params["nr"] = needs_review
    if verified is not None:
        where += " AND is_verified = :v"; params["v"] = verified
    if q:
        where += " AND (name ILIKE :q OR address_city ILIKE :q)"; params["q"] = f"%{q}%"

    rows = db.execute(text(f"""
        SELECT id, name, address_city, is_verified, is_active, needs_review, data_verified_at, rating_google
        FROM salons WHERE {where}
        ORDER BY needs_review DESC, created_at DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    total = db.execute(text(f"SELECT COUNT(*) FROM salons WHERE {where}"), params).scalar()
    return {"items": [dict(r) for r in rows], "total": total}


@router.patch("/salons/{salon_id}")
def update_salon(salon_id: int, updates: dict, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    allowed = {"is_active", "is_verified", "needs_review"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        raise HTTPException(400, "No valid fields")
    set_clause = ", ".join(f"{k} = :{k}" for k in filtered)
    db.execute(text(f"UPDATE salons SET {set_clause}, updated_at = NOW() WHERE id = :id"),
               {**filtered, "id": salon_id})
    db.commit()
    return {"status": "ok"}


@router.get("/professionals")
def list_professionals(
    page: int = 1, limit: int = 20,
    active_only: bool = False,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    where = "is_active = :active" if active_only else "1=1"
    params: dict = {"limit": limit, "offset": (page-1)*limit, "active": True}
    rows = db.execute(text(f"""
        SELECT id, name, specialty, base_city, is_active, is_verified, created_at
        FROM professionals WHERE {where}
        ORDER BY is_active ASC, created_at DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/professionals/{pro_id}")
def approve_professional(pro_id: int, is_active: bool, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    db.execute(text("UPDATE professionals SET is_active = :a WHERE id = :id"), {"a": is_active, "id": pro_id})
    db.commit()
    return {"status": "ok"}


@router.get("/claims")
def list_claims(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT ct.id, ct.salon_id, ct.expires_at, ct.used_at, ct.created_at,
               s.name AS salon_name, u.email AS user_email
        FROM claiming_tokens ct
        JOIN salons s ON ct.salon_id = s.id
        JOIN users u ON ct.user_id = u.id
        ORDER BY ct.created_at DESC LIMIT 100
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/reports")
def list_reports(status: str = "open", user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT r.id, r.reason, r.description, r.status, r.created_at,
               s.name AS salon_name, r.salon_id
        FROM reports r
        LEFT JOIN salons s ON r.salon_id = s.id
        WHERE r.status = :status
        ORDER BY r.created_at DESC LIMIT 100
    """), {"status": status}).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/reports/{report_id}")
def resolve_report(report_id: int, status: str, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if status not in ("resolved", "dismissed", "reviewed"):
        raise HTTPException(400, "Invalid status")
    db.execute(text("UPDATE reports SET status = :s, resolved_by = :uid, resolved_at = NOW() WHERE id = :id"),
               {"s": status, "uid": user.id, "id": report_id})
    db.commit()
    return {"status": "ok"}


@router.get("/moderation")
def moderation_queue(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, content_type, content_id, content_text, content_url,
               auto_flags, status, created_at
        FROM moderation_queue WHERE status = 'pending'
        ORDER BY created_at ASC LIMIT 50
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/moderation/{item_id}")
def resolve_moderation(item_id: int, status: str, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    if status not in ("approved", "rejected"):
        raise HTTPException(400)
    db.execute(text("""
        UPDATE moderation_queue SET status = :s, reviewed_by = :uid, reviewed_at = NOW() WHERE id = :id
    """), {"s": status, "uid": user.id, "id": item_id})
    db.commit()
    return {"status": "ok"}


@router.get("/users")
def list_users(page: int = 1, limit: int = 20, q: Optional[str] = None, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    where = "1=1"
    params: dict = {"limit": limit, "offset": (page-1)*limit}
    if q:
        where += " AND (email ILIKE :q OR name ILIKE :q)"; params["q"] = f"%{q}%"
    rows = db.execute(text(f"""
        SELECT id, email, name, role, is_active, is_email_verified, preferred_language, created_at
        FROM users WHERE {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), params).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/users/{user_id}")
def update_user(user_id: int, updates: dict, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    allowed = {"is_active", "role"}
    filtered = {k: v for k, v in updates.items() if k in allowed}
    if not filtered:
        raise HTTPException(400)
    set_clause = ", ".join(f"{k} = :{k}" for k in filtered)
    db.execute(text(f"UPDATE users SET {set_clause} WHERE id = :id"), {**filtered, "id": user_id})
    db.commit()
    return {"status": "ok"}
