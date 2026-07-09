"""Deduplication helpers — prevent saving the same salon twice."""
import re
import unicodedata
from rapidfuzz import fuzz
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Salon


def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    return re.sub(r"[^\d+]", "", phone)


def find_duplicate(session: Session, name: str, phone: str | None,
                   lat: float | None, lng: float | None,
                   google_place_id: str | None = None) -> Salon | None:
    # 1. Exact match by Google Place ID
    if google_place_id:
        existing = session.query(Salon).filter_by(google_place_id=google_place_id).first()
        if existing:
            return existing

    # 2. Match by normalized phone — DB-side strip, no full table scan
    norm_phone = normalize_phone(phone or "")
    if norm_phone and len(norm_phone) >= 8:
        rows = session.execute(
            text("SELECT id FROM salons WHERE regexp_replace(phone_primary, '[^\\d+]', '', 'g') = :p LIMIT 1"),
            {"p": norm_phone},
        ).fetchone()
        if rows:
            return session.get(Salon, rows[0])

    # 3. Fuzzy name match within ~500m radius
    if lat and lng:
        nearby = session.query(Salon).filter(
            Salon.lat.between(lat - 0.005, lat + 0.005),
            Salon.lng.between(lng - 0.005, lng + 0.005),
        ).all()
        norm_name = normalize(name)
        for s in nearby:
            score = fuzz.token_sort_ratio(norm_name, normalize(s.name))
            if score >= 85:
                return s

    return None
