from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import math
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

from app.core.database import get_db
from app.models.professional import Professional

router = APIRouter(prefix="/professionals", tags=["professionals"])

DAY_NAMES = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    day_of_week: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_available: bool

class PortfolioItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url_after: str
    url_before: Optional[str]
    caption: Optional[str]
    service_tag: Optional[str]
    is_featured: bool

class SocialLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    platform: str
    url: str

class ProfessionalListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: Optional[str]
    specialty: Optional[str]
    base_city: Optional[str]
    base_lat: Optional[float]
    base_lng: Optional[float]
    service_radius_km: int
    does_home_visits: bool
    has_home_studio: bool
    phone: Optional[str]
    rating_avg: Optional[Decimal]
    review_count: int
    price_level: Optional[int]
    is_verified: bool
    featured_photo: Optional[str] = None
    distance_km: Optional[float] = None

class ProfessionalDetail(ProfessionalListItem):
    bio: Optional[str]
    bio_el: Optional[str]
    bio_ru: Optional[str]
    bio_uk: Optional[str]
    instagram: Optional[str]
    email: Optional[str]
    portfolio: list[PortfolioItemOut] = []
    availability: list[AvailabilityOut] = []
    social_links: list[SocialLinkOut] = []

class PaginatedProfessionals(BaseModel):
    items: list[ProfessionalListItem]
    total: int
    page: int
    limit: int
    pages: int


def _featured_photo(pro: Professional) -> Optional[str]:
    if not pro.portfolio:
        return None
    featured = next((p for p in pro.portfolio if p.is_featured), None)
    return (featured or pro.portfolio[0]).url_after


@router.get("", response_model=PaginatedProfessionals)
def list_professionals(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    home_visits: Optional[bool] = None,
    home_studio: Optional[bool] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = Query(10.0),
    db: Session = Depends(get_db),
):
    q = db.query(Professional).filter(Professional.is_active == True)

    if city:
        q = q.filter(Professional.base_city.ilike(f"%{city}%"))
    if specialty:
        q = q.filter(Professional.specialty.ilike(f"%{specialty}%"))
    if home_visits is not None:
        q = q.filter(Professional.does_home_visits == home_visits)
    if home_studio is not None:
        q = q.filter(Professional.has_home_studio == home_studio)

    total = q.count()
    pros = (
        q.order_by(Professional.rating_avg.desc().nullslast(), Professional.review_count.desc())
        .offset((page - 1) * limit).limit(limit).all()
    )

    items = []
    for p in pros:
        item = ProfessionalListItem.model_validate(p)
        item.featured_photo = _featured_photo(p)
        items.append(item)

    return PaginatedProfessionals(
        items=items, total=total, page=page, limit=limit,
        pages=math.ceil(total / limit) if total else 1,
    )


@router.get("/{pro_id}", response_model=ProfessionalDetail)
def get_professional(pro_id: int | str, db: Session = Depends(get_db)):
    if isinstance(pro_id, str) and not pro_id.isdigit():
        pro = db.query(Professional).filter(Professional.slug == pro_id, Professional.is_active == True).first()
    else:
        pro = db.query(Professional).filter(Professional.id == int(pro_id), Professional.is_active == True).first()

    if not pro:
        raise HTTPException(status_code=404, detail="Professional not found")

    detail = ProfessionalDetail.model_validate(pro)
    detail.featured_photo = _featured_photo(pro)

    # Sort portfolio: featured first, then by sort_order
    detail.portfolio = sorted(
        [PortfolioItemOut.model_validate(p) for p in pro.portfolio],
        key=lambda x: (not x.is_featured, 0)
    )
    detail.availability = [AvailabilityOut.model_validate(a) for a in pro.availability]
    detail.social_links = [SocialLinkOut.model_validate(s) for s in pro.social_links]
    return detail
