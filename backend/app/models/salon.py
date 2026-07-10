from datetime import datetime
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Boolean,
    Numeric, Double, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Salon(Base):
    __tablename__ = "salons"

    id              = Column(Integer, primary_key=True)
    name            = Column(String(255), nullable=False)
    name_el         = Column(String(255))
    slug            = Column(String(300), unique=True)
    description     = Column(Text)
    description_el  = Column(Text)
    description_ru  = Column(Text)
    description_uk  = Column(Text)

    address_street   = Column(String(255))
    address_number   = Column(String(30))
    address_city     = Column(String(120))
    address_district = Column(String(120), index=True)
    address_region   = Column(String(120))
    address_postal   = Column(String(20))
    address_full     = Column(Text)
    lat             = Column(Double)
    lng             = Column(Double)
    google_place_id = Column(String(100), unique=True)

    phone_primary   = Column(String(30))
    phone_secondary = Column(String(30))
    email           = Column(String(255))
    website         = Column(String(500))

    rating_google   = Column(Numeric(3, 2))
    rating_count    = Column(Integer, default=0)
    price_level     = Column(SmallInteger)
    is_verified     = Column(Boolean, default=False)
    is_active       = Column(Boolean, default=True)
    needs_review    = Column(Boolean, default=False)

    data_verified_at    = Column(DateTime)
    contact_verified_at = Column(DateTime)
    hours_verified_at   = Column(DateTime)
    services_verified_at = Column(DateTime)
    photos_verified_at  = Column(DateTime)
    last_source         = Column(String(80))

    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hours       = relationship("SalonHour",    back_populates="salon", cascade="all,delete")
    photos      = relationship("Photo",        back_populates="salon", cascade="all,delete")
    services    = relationship("Service",      back_populates="salon", cascade="all,delete")
    reviews     = relationship("Review",       back_populates="salon", cascade="all,delete")
    social_links = relationship("SocialLink",  back_populates="salon", cascade="all,delete")
    staff       = relationship("Staff",        back_populates="salon", cascade="all,delete")


class SalonHour(Base):
    __tablename__ = "salon_hours"
    __table_args__ = (UniqueConstraint("salon_id", "day_of_week"),)

    id          = Column(Integer, primary_key=True)
    salon_id    = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 0=Mon, 6=Sun
    open_time   = Column(String(5))   # "09:00"
    close_time  = Column(String(5))
    is_closed   = Column(Boolean, default=False)

    salon = relationship("Salon", back_populates="hours")


class Photo(Base):
    __tablename__ = "photos"

    id         = Column(Integer, primary_key=True)
    salon_id   = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    url        = Column(String(1000), nullable=False)
    caption    = Column(String(255))
    is_primary = Column(Boolean, default=False)
    source     = Column(String(80))
    width      = Column(Integer)
    height     = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="photos")


class Service(Base):
    __tablename__ = "services"

    id           = Column(Integer, primary_key=True)
    salon_id     = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    category_id  = Column(Integer, ForeignKey("service_categories.id"))
    name         = Column(String(255), nullable=False)
    name_el      = Column(String(255))
    name_en      = Column(Text)
    name_ru      = Column(Text)
    name_uk      = Column(Text)
    description  = Column(Text)
    duration_min = Column(Integer)
    price_from   = Column(Numeric(10, 2))
    price_to     = Column(Numeric(10, 2))
    currency     = Column(String(3), default="EUR")
    is_active    = Column(Boolean, default=True)

    salon = relationship("Salon", back_populates="services")


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id         = Column(Integer, primary_key=True)
    slug       = Column(String(80), unique=True, nullable=False)
    name_en    = Column(String(120), nullable=False)
    name_el    = Column(String(120))
    parent_id  = Column(Integer, ForeignKey("service_categories.id"))
    icon       = Column(String(80))
    sort_order = Column(Integer, default=0)


class SalonCategory(Base):
    __tablename__ = "salon_categories"

    salon_id    = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("service_categories.id", ondelete="CASCADE"), primary_key=True)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("source", "source_id"),)

    id           = Column(Integer, primary_key=True)
    salon_id     = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    source       = Column(String(80), nullable=False)
    source_id    = Column(String(255))
    author_name  = Column(String(255))
    rating       = Column(SmallInteger)
    text         = Column(Text)
    text_en      = Column(Text)
    text_ru      = Column(Text)
    text_uk      = Column(Text)
    published_at = Column(DateTime)
    created_at   = Column(DateTime, default=datetime.utcnow)

    salon = relationship("Salon", back_populates="reviews")


class SocialLink(Base):
    __tablename__ = "social_links"
    __table_args__ = (UniqueConstraint("salon_id", "platform"),)

    id       = Column(Integer, primary_key=True)
    salon_id = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    url      = Column(String(500), nullable=False)

    salon = relationship("Salon", back_populates="social_links")


class Staff(Base):
    __tablename__ = "staff"

    id        = Column(Integer, primary_key=True)
    salon_id  = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    name      = Column(String(255), nullable=False)
    bio       = Column(Text)
    role      = Column(String(120))
    photo_url = Column(String(500))
    is_active = Column(Boolean, default=True)

    salon = relationship("Salon", back_populates="staff")
