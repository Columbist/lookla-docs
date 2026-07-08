from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime, time, date
from decimal import Decimal


class SalonHourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    day_of_week: int
    open_time: Optional[time]
    close_time: Optional[time]
    is_closed: bool

    @field_serializer("open_time", "close_time")
    def serialize_time(self, v: Optional[time]) -> Optional[str]:
        return v.strftime("%H:%M") if v else None


class PhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    url: str
    caption: Optional[str]
    is_primary: bool
    width: Optional[int]
    height: Optional[int]


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    name_el: Optional[str]
    description: Optional[str]
    duration_min: Optional[int]
    price_from: Optional[Decimal]
    price_to: Optional[Decimal]
    currency: str


class SocialLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    platform: str
    url: str


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    author_name: Optional[str]
    rating: Optional[int]
    text: Optional[str]
    published_at: Optional[date]

    @field_serializer("published_at")
    def serialize_date(self, v: Optional[date]) -> Optional[str]:
        return v.isoformat() if v else None


class SalonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: Optional[str]
    address_city: Optional[str]
    address_street: Optional[str]
    address_number: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    phone_primary: Optional[str]
    rating_google: Optional[Decimal]
    rating_count: int
    price_level: Optional[int]
    is_verified: bool
    primary_photo: Optional[str] = None
    description_lang: Optional[str] = None
    min_price: Optional[float] = None
    is_open_now: Optional[bool] = None


class SalonDetail(SalonListItem):
    name_el: Optional[str]
    description: Optional[str]
    description_el: Optional[str]
    description_ru: Optional[str]
    description_uk: Optional[str]
    address_full: Optional[str]
    address_region: Optional[str]
    address_postal: Optional[str]
    email: Optional[str]
    website: Optional[str]
    data_verified_at: Optional[datetime]
    hours: list[SalonHourOut] = []
    photos: list[PhotoOut] = []
    services: list[ServiceOut] = []
    social_links: list[SocialLinkOut] = []
    reviews: list[ReviewOut] = []
    review_count: int = 0


class PaginatedSalons(BaseModel):
    items: list[SalonListItem]
    total: int
    page: int
    limit: int
    pages: int


class SearchResult(BaseModel):
    type: str  # "salon" | "professional"
    id: int
    name: str
    slug: Optional[str]
    address_city: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    phone_primary: Optional[str]
    rating_google: Optional[Decimal]
    price_level: Optional[int]
    primary_photo: Optional[str]
    distance_km: Optional[float] = None
