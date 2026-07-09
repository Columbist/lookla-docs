"""SQLAlchemy ORM models — mirrors db/init.sql."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, SmallInteger, String, Text, Boolean, Numeric,
    Double, DateTime, Date, Time, ForeignKey, UniqueConstraint, JSON,
    create_engine, text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import os

Base = declarative_base()


def get_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ.get('DB_HOST','localhost')}:{os.environ.get('DB_PORT','5432')}"
        f"/{os.environ['DB_NAME']}"
    )
    return create_engine(url, pool_pre_ping=True)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


class Salon(Base):
    __tablename__ = "salons"

    id               = Column(Integer, primary_key=True)
    name             = Column(String(255), nullable=False)
    name_el          = Column(String(255))
    slug             = Column(String(300), unique=True)
    description      = Column(Text)
    description_el   = Column(Text)

    address_street   = Column(String(255))
    address_number   = Column(String(30))
    address_city     = Column(String(120))
    address_region   = Column(String(120))
    address_postal   = Column(String(20))
    address_full     = Column(Text)
    lat              = Column(Double)
    lng              = Column(Double)
    google_place_id  = Column(String(100), unique=True)

    phone_primary    = Column(String(30))
    phone_secondary  = Column(String(30))
    email            = Column(String(255))
    website          = Column(String(500))

    rating_google    = Column(Numeric(3, 2))
    rating_count     = Column(Integer, default=0)
    price_level      = Column(SmallInteger)
    is_verified      = Column(Boolean, default=False)
    is_active        = Column(Boolean, default=True)

    # Data freshness — section-level timestamps
    contact_verified_at  = Column(DateTime)   # phone/email/website last confirmed
    hours_verified_at    = Column(DateTime)   # opening hours last confirmed
    services_verified_at = Column(DateTime)   # services + prices last confirmed
    photos_verified_at   = Column(DateTime)   # photos last confirmed
    data_verified_at     = Column(DateTime)   # max of all above; shown to end users
    last_source          = Column(String(80)) # which spider last touched this record

    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hours            = relationship("SalonHour",   back_populates="salon", cascade="all,delete")
    services         = relationship("Service",     back_populates="salon", cascade="all,delete")
    photos           = relationship("Photo",       back_populates="salon", cascade="all,delete")
    reviews          = relationship("Review",      back_populates="salon", cascade="all,delete")
    social_links     = relationship("SocialLink",  back_populates="salon", cascade="all,delete")
    crawler_sources  = relationship("CrawlerSource", back_populates="salon")


class SalonHour(Base):
    __tablename__ = "salon_hours"
    __table_args__ = (UniqueConstraint("salon_id", "day_of_week"),)

    id          = Column(Integer, primary_key=True)
    salon_id    = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)  # 0=Mon, 6=Sun
    open_time   = Column(Time)
    close_time  = Column(Time)
    is_closed   = Column(Boolean, default=False)

    salon = relationship("Salon", back_populates="hours")


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id        = Column(Integer, primary_key=True)
    slug      = Column(String(80), unique=True, nullable=False)
    name_en   = Column(String(120), nullable=False)
    name_el   = Column(String(120))
    parent_id = Column(Integer, ForeignKey("service_categories.id"))
    icon      = Column(String(80))
    sort_order = Column(Integer, default=0)


class Service(Base):
    __tablename__ = "services"

    id           = Column(Integer, primary_key=True)
    salon_id     = Column(Integer, ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    category_id  = Column(Integer, ForeignKey("service_categories.id"))
    name         = Column(String(255), nullable=False)
    name_el      = Column(String(255))
    description  = Column(Text)
    duration_min = Column(Integer)
    price_from   = Column(Numeric(10, 2))
    price_to     = Column(Numeric(10, 2))
    currency     = Column(String(3), default="EUR")
    is_active    = Column(Boolean, default=True)
    source       = Column(String(80))
    source_id    = Column(String(255))

    salon = relationship("Salon", back_populates="services")


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
    published_at = Column(Date)
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


class CrawlerSource(Base):
    __tablename__ = "crawler_sources"
    __table_args__ = (UniqueConstraint("source", "source_id"),)

    id              = Column(Integer, primary_key=True)
    salon_id        = Column(Integer, ForeignKey("salons.id", ondelete="SET NULL"))
    source          = Column(String(80), nullable=False)
    source_id       = Column(String(255))
    source_url      = Column(String(1000))
    last_crawled_at = Column(DateTime)
    crawl_status    = Column(String(30), default="pending")
    error_message   = Column(Text)
    raw_data        = Column(JSON)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    salon = relationship("Salon", back_populates="crawler_sources")
