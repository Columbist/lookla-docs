from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_
from typing import Optional
import math

from app.core.database import get_db
from app.models.salon import Salon, SalonHour, Photo, Service, Review, SocialLink
from app.schemas.salon import SalonListItem, SalonDetail, PaginatedSalons, PhotoOut

router = APIRouter(prefix="/salons", tags=["salons"])

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _primary_photo(salon: Salon) -> Optional[str]:
    if not salon.photos:
        return None
    primary = next((p for p in salon.photos if p.is_primary), None)
    return (primary or salon.photos[0]).url


@router.get("", response_model=PaginatedSalons)
def list_salons(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    price_level: Optional[int] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Salon).filter(Salon.is_active == True)

    if city:
        q = q.filter(Salon.address_city.ilike(f"%{city}%"))
    if min_rating:
        q = q.filter(Salon.rating_google >= min_rating)
    if price_level:
        q = q.filter(Salon.price_level == price_level)
    if verified_only:
        q = q.filter(Salon.is_verified == True)

    total = q.count()
    salons = (
        q.order_by(Salon.rating_google.desc().nullslast(), Salon.rating_count.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for s in salons:
        item = SalonListItem.model_validate(s)
        item.primary_photo = _primary_photo(s)
        items.append(item)

    return PaginatedSalons(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit),
    )


@router.get("/{salon_id}", response_model=SalonDetail)
def get_salon(salon_id: int | str, db: Session = Depends(get_db)):
    if isinstance(salon_id, str) and not salon_id.isdigit():
        salon = db.query(Salon).filter(Salon.slug == salon_id, Salon.is_active == True).first()
    else:
        salon = db.query(Salon).filter(Salon.id == int(salon_id), Salon.is_active == True).first()

    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    detail = SalonDetail.model_validate(salon)
    detail.primary_photo = _primary_photo(salon)
    detail.review_count = len(salon.reviews)
    return detail


@router.get("/{salon_id}/photos", response_model=list[PhotoOut])
def get_photos(salon_id: int, db: Session = Depends(get_db)):
    salon = db.query(Salon).filter(Salon.id == salon_id, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    return [PhotoOut.model_validate(p) for p in salon.photos]
