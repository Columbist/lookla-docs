from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db
from app.schemas.salon import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
def search(
    q: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(5.0, ge=0.5, le=50),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Unified search: returns salons (and professionals later).
    Supports: full-text (q), city filter, geo radius (lat/lng).
    """
    conditions = ["s.is_active = true"]
    params: dict = {"limit": limit}

    if city:
        conditions.append("s.address_city ILIKE :city")
        params["city"] = f"%{city}%"

    if q:
        conditions.append(
            "to_tsvector('simple', unaccent(coalesce(s.name,'') || ' ' || coalesce(s.name_el,'') || ' ' || coalesce(s.address_city,''))) "
            "@@ plainto_tsquery('simple', unaccent(:q))"
        )
        params["q"] = q

    if category:
        conditions.append(
            "(s.name ILIKE :cat OR s.description ILIKE :cat)"
        )
        params["cat"] = f"%{category}%"

    # Haversine distance (no PostGIS required)
    haversine = (
        "6371.0 * acos(LEAST(1.0, "
        "cos(radians(:lat)) * cos(radians(s.lat)) * "
        "cos(radians(s.lng) - radians(:lng)) + "
        "sin(radians(:lat)) * sin(radians(s.lat))"
        "))"
    )

    distance_expr = "NULL::float AS distance_km"
    order_by = "s.rating_google DESC NULLS LAST, s.rating_count DESC"

    if lat and lng:
        params["lat"] = lat
        params["lng"] = lng
        conditions.append(
            f"s.lat IS NOT NULL AND s.lng IS NOT NULL AND {haversine} <= :radius_km"
        )
        params["radius_km"] = radius_km
        distance_expr = f"ROUND(CAST({haversine} AS numeric), 2) AS distance_km"
        order_by = haversine + " ASC"

    where = " AND ".join(conditions)

    sql = text(f"""
        SELECT
            'salon'::text AS type,
            s.id,
            s.name,
            s.slug,
            s.address_city,
            s.lat,
            s.lng,
            s.phone_primary,
            s.rating_google,
            s.price_level,
            (SELECT p.url FROM photos p WHERE p.salon_id = s.id AND p.is_primary = true LIMIT 1)
                AS primary_photo,
            {distance_expr}
        FROM salons s
        WHERE {where}
        ORDER BY {order_by}
        LIMIT :limit
    """)

    rows = db.execute(sql, params).mappings().all()
    return [SearchResult(**dict(row)) for row in rows]
