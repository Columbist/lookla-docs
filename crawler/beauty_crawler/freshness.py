"""
Data freshness tracking and display helpers.

Each spider calls stamp() when it successfully reads/updates a salon.
The frontend (phase 2) calls label() / badge() to render "Updated X days ago".

Freshness sections:
  contact  — phone, email, website
  hours    — opening hours
  services — service list + prices
  photos   — photo URLs

data_verified_at is auto-maintained by the DB trigger as max of all sections,
but we also keep it in sync here so in-memory objects reflect the latest value.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from .models import Salon

Section = Literal["contact", "hours", "services", "photos"]

# Thresholds for the freshness badge (days since last verification)
_FRESH_DAYS   = 30   # green  — "Updated N days ago"
_STALE_DAYS   = 90   # yellow — "Updated N weeks ago"
_OUTDATED_DAYS = 180 # orange — "Updated N months ago"
                     # red    — anything older: "May be outdated"


def stamp(
    salon: Salon,
    source: str,
    sections: list[Section],
    now: datetime | None = None,
) -> None:
    """
    Mark one or more data sections as freshly verified.
    Call this inside every spider after a successful save or update.

    Example:
        stamp(salon, source="google_places", sections=["contact", "hours", "photos"])
    """
    ts = now or datetime.now(timezone.utc).replace(tzinfo=None)

    def _naive(dt: datetime | None) -> datetime | None:
        return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt

    if "contact"  in sections:
        salon.contact_verified_at  = ts
    if "hours"    in sections:
        salon.hours_verified_at    = ts
    if "services" in sections:
        salon.services_verified_at = ts
    if "photos"   in sections:
        salon.photos_verified_at   = ts

    # Keep data_verified_at in sync (DB trigger also does this, belt-and-suspenders)
    salon.data_verified_at = max(
        filter(None, [
            _naive(salon.contact_verified_at),
            _naive(salon.hours_verified_at),
            _naive(salon.services_verified_at),
            _naive(salon.photos_verified_at),
        ]),
        default=ts,
    )
    salon.last_source = source


def freshness_label(verified_at: datetime | None) -> str:
    """
    Human-readable freshness string for display in the UI.

    Examples:
        "Updated today"
        "Updated 3 days ago"
        "Updated 2 weeks ago"
        "Updated 4 months ago"
        "May be outdated"
        "No data yet"
    """
    if not verified_at:
        return "No data yet"

    now  = datetime.utcnow()
    diff = now - verified_at
    days = diff.days

    if days == 0:
        return "Updated today"
    if days == 1:
        return "Updated yesterday"
    if days < 7:
        return f"Updated {days} days ago"
    if days < 30:
        weeks = days // 7
        return f"Updated {weeks} week{'s' if weeks > 1 else ''} ago"
    if days < 365:
        months = days // 30
        return f"Updated {months} month{'s' if months > 1 else ''} ago"

    years = days // 365
    return f"Updated {years} year{'s' if years > 1 else ''} ago"


def freshness_badge(verified_at: datetime | None) -> dict:
    """
    Returns a dict ready to serialize to JSON for the frontend badge:
      {
        "label": "Updated 3 days ago",
        "level": "fresh",         # fresh | ok | stale | outdated
        "color": "#27ae60",
        "days":  3,
      }
    Levels map to UI colors:
      fresh    → green  (≤ 30 days)
      ok       → teal   (31–90 days)
      stale    → orange (91–180 days)
      outdated → red    (> 180 days or None)
    """
    label = freshness_label(verified_at)

    if not verified_at:
        return {"label": label, "level": "outdated", "color": "#e74c3c", "days": None}

    days = (datetime.utcnow() - verified_at).days

    if days <= _FRESH_DAYS:
        level, color = "fresh",    "#27ae60"
    elif days <= _STALE_DAYS:
        level, color = "ok",       "#2ecc71"
    elif days <= _OUTDATED_DAYS:
        level, color = "stale",    "#e67e22"
    else:
        level, color = "outdated", "#e74c3c"

    return {"label": label, "level": level, "color": color, "days": days}


def section_badges(salon: Salon) -> dict[str, dict]:
    """
    Returns freshness badges for each data section of a salon.
    Useful for a detailed "data quality" panel in the admin UI.

    Example return:
      {
        "contact":  {"label": "Updated 2 days ago", "level": "fresh", ...},
        "hours":    {"label": "Updated 5 weeks ago", "level": "ok", ...},
        "services": {"label": "May be outdated", "level": "outdated", ...},
        "photos":   {"label": "Updated today", "level": "fresh", ...},
      }
    """
    return {
        "contact":  freshness_badge(salon.contact_verified_at),
        "hours":    freshness_badge(salon.hours_verified_at),
        "services": freshness_badge(salon.services_verified_at),
        "photos":   freshness_badge(salon.photos_verified_at),
    }


def salons_needing_refresh(
    session: Session,
    older_than_days: int = 30,
    limit: int = 500,
) -> list[Salon]:
    """
    Returns salons whose data_verified_at is older than `older_than_days`
    (or NULL). Used by the scheduler to prioritise re-crawls.
    """
    from datetime import timedelta
    from sqlalchemy import or_
    cutoff = datetime.utcnow() - timedelta(days=older_than_days)
    return (
        session.query(Salon)
        .filter(
            Salon.is_active == True,
            or_(Salon.data_verified_at < cutoff, Salon.data_verified_at.is_(None)),
        )
        .order_by(Salon.data_verified_at.asc().nullsfirst())
        .limit(limit)
        .all()
    )
