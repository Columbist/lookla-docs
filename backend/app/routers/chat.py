"""
In-app messaging: conversations between clients and salons/professionals.
Also handles availability requests (soft booking inquiry → confirmed slot).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/chat", tags=["chat"])


# ─────────────────────────── Schemas ──────────────────────────────────────────

class MessageIn(BaseModel):
    body: Optional[str] = None
    attachment_url: Optional[str] = None
    message_type: str = "text"      # text | image | slot_proposal
    proposed_slot: Optional[datetime] = None


class AvailabilityRequestIn(BaseModel):
    salon_id: Optional[int] = None
    professional_id: Optional[int] = None
    service_notes: Optional[str] = None
    preferred_dates: Optional[str] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None


class ProposeSlotIn(BaseModel):
    request_id: int
    proposed_slot: datetime
    reply_text: Optional[str] = None


# ─────────────────────────── Conversations ────────────────────────────────────

@router.post("/conversations", status_code=201)
def start_conversation(
    salon_id: Optional[int] = None,
    professional_id: Optional[int] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start or get existing conversation between client and salon/professional."""
    if not salon_id and not professional_id:
        raise HTTPException(400, "salon_id or professional_id required")

    # Check for existing conversation
    if salon_id:
        existing = db.execute(text("""
            SELECT id FROM conversations
            WHERE client_user_id = :uid AND salon_id = :sid
        """), {"uid": user.id, "sid": salon_id}).first()
    else:
        existing = db.execute(text("""
            SELECT id FROM conversations
            WHERE client_user_id = :uid AND professional_id = :pid
        """), {"uid": user.id, "pid": professional_id}).first()

    if existing:
        return {"id": existing.id, "created": False}

    conv_id = db.execute(text("""
        INSERT INTO conversations (client_user_id, salon_id, professional_id)
        VALUES (:uid, :sid, :pid) RETURNING id
    """), {"uid": user.id, "sid": salon_id, "pid": professional_id}).scalar()
    db.commit()

    return {"id": conv_id, "created": True}


@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all conversations for current user (client or owner)."""
    # As client
    client_convs = db.execute(text("""
        SELECT c.id, c.last_message_at, c.client_unread,
               s.name AS other_name, s.id AS salon_id, NULL AS pro_id,
               (SELECT body FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_body
        FROM conversations c
        LEFT JOIN salons s ON c.salon_id = s.id
        WHERE c.client_user_id = :uid
        UNION ALL
        SELECT c.id, c.last_message_at, c.client_unread,
               p.name AS other_name, NULL AS salon_id, p.id AS pro_id,
               (SELECT body FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_body
        FROM conversations c
        LEFT JOIN professionals p ON c.professional_id = p.id
        WHERE c.client_user_id = :uid AND c.professional_id IS NOT NULL
        ORDER BY last_message_at DESC NULLS LAST
    """), {"uid": user.id}).mappings().all()

    # As owner (salon side)
    owner_convs = db.execute(text("""
        SELECT c.id, c.last_message_at, c.owner_unread AS client_unread,
               u.name AS other_name, c.salon_id, NULL AS pro_id,
               (SELECT body FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) AS last_body
        FROM conversations c
        JOIN salon_owners so ON c.salon_id = so.salon_id
        JOIN users u ON c.client_user_id = u.id
        WHERE so.user_id = :uid
        ORDER BY last_message_at DESC NULLS LAST
        LIMIT 50
    """), {"uid": user.id}).mappings().all()

    all_convs = [dict(r) for r in client_convs] + [dict(r) for r in owner_convs]
    # Deduplicate by id
    seen = set()
    result = []
    for c in all_convs:
        if c["id"] not in seen:
            seen.add(c["id"])
            result.append(c)

    return sorted(result, key=lambda x: x.get("last_message_at") or datetime.min, reverse=True)


@router.get("/conversations/{conv_id}/messages")
def get_messages(
    conv_id: int,
    before_id: Optional[int] = None,
    limit: int = Query(50, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get messages in a conversation, paginated (cursor-based)."""
    _check_access(user.id, conv_id, db)

    where = "m.conversation_id = :cid"
    params: dict = {"cid": conv_id, "limit": limit}
    if before_id:
        where += " AND m.id < :before_id"
        params["before_id"] = before_id

    messages = db.execute(text(f"""
        SELECT m.id, m.body, m.attachment_url, m.message_type,
               m.proposed_slot, m.read_at, m.created_at,
               m.sender_user_id,
               u.name AS sender_name
        FROM messages m
        JOIN users u ON m.sender_user_id = u.id
        WHERE {where}
        ORDER BY m.id DESC
        LIMIT :limit
    """), params).mappings().all()

    # Mark as read
    db.execute(text("""
        UPDATE messages SET read_at = NOW()
        WHERE conversation_id = :cid AND sender_user_id != :uid AND read_at IS NULL
    """), {"cid": conv_id, "uid": user.id})

    # Reset unread counter for this user
    conv = db.execute(text("SELECT client_user_id FROM conversations WHERE id = :id"), {"id": conv_id}).first()
    if conv and conv.client_user_id == user.id:
        db.execute(text("UPDATE conversations SET client_unread = 0 WHERE id = :id"), {"id": conv_id})
    else:
        db.execute(text("UPDATE conversations SET owner_unread = 0 WHERE id = :id"), {"id": conv_id})

    db.commit()

    return list(reversed([dict(m) for m in messages]))


@router.post("/conversations/{conv_id}/messages", status_code=201)
def send_message(
    conv_id: int,
    body: MessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_access(user.id, conv_id, db)

    if not body.body and not body.attachment_url:
        raise HTTPException(400, "Message must have body or attachment")

    msg_id = db.execute(text("""
        INSERT INTO messages (conversation_id, sender_user_id, body, attachment_url, message_type, proposed_slot)
        VALUES (:cid, :uid, :body, :att, :type, :slot)
        RETURNING id
    """), {
        "cid": conv_id, "uid": user.id,
        "body": body.body, "att": body.attachment_url,
        "type": body.message_type, "slot": body.proposed_slot,
    }).scalar()

    # Update conversation timestamp + unread counter for other party
    conv = db.execute(text("""
        SELECT client_user_id FROM conversations WHERE id = :id
    """), {"id": conv_id}).first()

    if conv:
        if conv.client_user_id == user.id:
            # Sender is client → increment owner unread
            db.execute(text("""
                UPDATE conversations SET last_message_at = NOW(), owner_unread = owner_unread + 1
                WHERE id = :id
            """), {"id": conv_id})
        else:
            # Sender is owner → increment client unread
            db.execute(text("""
                UPDATE conversations SET last_message_at = NOW(), client_unread = client_unread + 1
                WHERE id = :id
            """), {"id": conv_id})

    db.commit()
    return {"id": msg_id, "status": "sent"}


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Total unread messages for current user."""
    client_unread = db.execute(text("""
        SELECT COALESCE(SUM(client_unread), 0)
        FROM conversations WHERE client_user_id = :uid
    """), {"uid": user.id}).scalar()

    owner_unread = db.execute(text("""
        SELECT COALESCE(SUM(c.owner_unread), 0)
        FROM conversations c
        JOIN salon_owners so ON c.salon_id = so.salon_id
        WHERE so.user_id = :uid
    """), {"uid": user.id}).scalar()

    return {"total": int(client_unread or 0) + int(owner_unread or 0)}


# ─────────────────────────── Availability Requests ───────────────────────────

@router.post("/availability-requests", status_code=201)
def create_availability_request(
    body: AvailabilityRequestIn,
    user: Optional[User] = Depends(lambda db=None: None),   # optional auth
    db: Session = Depends(get_db),
):
    """Client requests available time from salon/professional (soft inquiry)."""
    req_id = db.execute(text("""
        INSERT INTO availability_requests
          (client_user_id, salon_id, professional_id, service_notes, preferred_dates, client_name, client_phone)
        VALUES (:uid, :sid, :pid, :notes, :dates, :name, :phone)
        RETURNING id
    """), {
        "uid": getattr(user, "id", None),
        "sid": body.salon_id, "pid": body.professional_id,
        "notes": body.service_notes, "dates": body.preferred_dates,
        "name": body.client_name, "phone": body.client_phone,
    }).scalar()
    db.commit()
    return {"id": req_id, "status": "pending"}


@router.get("/availability-requests/owner")
def owner_requests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Owner sees incoming availability requests for their salons."""
    rows = db.execute(text("""
        SELECT ar.id, ar.service_notes, ar.preferred_dates, ar.status,
               ar.client_name, ar.client_phone, ar.created_at,
               ar.proposed_slot, ar.reply_text,
               s.name AS salon_name, u.name AS client_user_name
        FROM availability_requests ar
        LEFT JOIN salons s ON ar.salon_id = s.id
        LEFT JOIN salon_owners so ON s.id = so.salon_id
        LEFT JOIN users u ON ar.client_user_id = u.id
        WHERE so.user_id = :uid AND ar.status = 'pending'
        ORDER BY ar.created_at DESC
    """), {"uid": user.id}).mappings().all()
    return [dict(r) for r in rows]


@router.post("/availability-requests/{req_id}/propose")
def propose_slot(req_id: int, body: ProposeSlotIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Owner proposes a specific time slot for the request."""
    db.execute(text("""
        UPDATE availability_requests
        SET status = 'replied', proposed_slot = :slot, reply_text = :text, updated_at = NOW()
        WHERE id = :id
    """), {"id": req_id, "slot": body.proposed_slot, "text": body.reply_text})
    db.commit()
    return {"status": "ok", "message": "Client will be notified of proposed slot"}


@router.post("/availability-requests/{req_id}/confirm")
def confirm_slot(req_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Client confirms the proposed slot → creates appointment."""
    req = db.execute(text("""
        SELECT * FROM availability_requests WHERE id = :id AND status = 'replied'
    """), {"id": req_id}).first()

    if not req:
        raise HTTPException(404, "Request not found or not in replied state")

    # Create appointment
    from datetime import timedelta
    ends_at = req.proposed_slot + timedelta(hours=1)  # default 1h
    appt_id = db.execute(text("""
        INSERT INTO appointments
          (salon_id, professional_id, client_user_id, client_name, client_phone,
           starts_at, ends_at, duration_min, status, source)
        VALUES (:sid, :pid, :uid, :name, :phone, :start, :end, 60, 'confirmed', 'availability_request')
        RETURNING id
    """), {
        "sid": req.salon_id, "pid": req.professional_id,
        "uid": req.client_user_id,
        "name": req.client_name, "phone": req.client_phone,
        "start": req.proposed_slot, "end": ends_at,
    }).scalar()

    db.execute(text("UPDATE availability_requests SET status = 'converted', updated_at = NOW() WHERE id = :id"), {"id": req_id})
    db.commit()

    return {"status": "ok", "appointment_id": appt_id}


# ─────────────────────────── Helpers ─────────────────────────────────────────

def _check_access(user_id: int, conv_id: int, db: Session):
    """Verify user has access to this conversation (client or salon owner)."""
    conv = db.execute(text("""
        SELECT c.client_user_id,
               EXISTS(
                   SELECT 1 FROM salon_owners so
                   WHERE so.salon_id = c.salon_id AND so.user_id = :uid
               ) AS is_owner,
               EXISTS(
                   SELECT 1 FROM professionals p
                   WHERE p.id = c.professional_id AND p.user_id = :uid
               ) AS is_pro
        FROM conversations c WHERE c.id = :cid
    """), {"cid": conv_id, "uid": user_id}).first()

    if not conv:
        raise HTTPException(404, "Conversation not found")
    if conv.client_user_id != user_id and not conv.is_owner and not conv.is_pro:
        raise HTTPException(403, "Access denied")
