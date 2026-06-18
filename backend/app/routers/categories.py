from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db

router = APIRouter(tags=["categories"])

LANG_FIELD = {"el": "name_el", "en": "name_en", "ru": "name_en", "uk": "name_en"}


@router.get("/api/categories")
def get_categories(lang: str = Query("el"), db: Session = Depends(get_db)):
    name_col = LANG_FIELD.get(lang, "name_en")
    rows = db.execute(text(f"""
        SELECT id, slug, {name_col} AS name, name_en, parent_id, icon, sort_order
        FROM service_categories
        ORDER BY sort_order, id
    """)).mappings().all()

    # Build tree: top-level + children
    top = [dict(r) | {"children": []} for r in rows if r["parent_id"] is None]
    by_id = {r["id"]: next((t for t in top if t["id"] == r["id"]), None) for r in rows}

    for r in rows:
        if r["parent_id"] is not None:
            parent = next((t for t in top if t["id"] == r["parent_id"]), None)
            if parent:
                parent["children"].append(dict(r))

    return top


@router.get("/api/cities")
def get_cities(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT address_city AS city, COUNT(*) AS count
        FROM salons
        WHERE is_active = true AND address_city IS NOT NULL
        GROUP BY address_city ORDER BY count DESC LIMIT 50
    """)).all()
    return [{"city": r[0], "count": r[1]} for r in rows]


@router.get("/api/sitemap-data")
def get_sitemap_data(db: Session = Depends(get_db)):
    salons = db.execute(text("""
        SELECT slug, updated_at FROM salons
        WHERE is_active = true AND slug IS NOT NULL
        ORDER BY updated_at DESC
    """)).all()
    pros = db.execute(text("""
        SELECT slug, updated_at FROM professionals
        WHERE is_active = true AND slug IS NOT NULL
        ORDER BY updated_at DESC
    """)).all()
    return {
        "salons": [{"slug": r[0], "updated_at": r[1]} for r in salons if r[0]],
        "professionals": [{"slug": r[0], "updated_at": r[1]} for r in pros if r[0]],
    }
