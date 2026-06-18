from datetime import datetime
from sqlalchemy import Column, Integer, SmallInteger, String, Text, Boolean, Numeric, Double, DateTime, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Professional(Base):
    __tablename__ = "professionals"

    id               = Column(Integer, primary_key=True)
    user_id          = Column(Integer, ForeignKey("users.id"))
    name             = Column(String(255), nullable=False)
    slug             = Column(String(300), unique=True)
    specialty        = Column(String(120))
    bio              = Column(Text)
    bio_el           = Column(Text)
    bio_ru           = Column(Text)
    bio_uk           = Column(Text)
    phone            = Column(String(30))
    instagram        = Column(String(100))
    email            = Column(String(255))
    base_city        = Column(String(120))
    base_lat         = Column(Double)
    base_lng         = Column(Double)
    service_radius_km = Column(Integer, default=15)
    does_home_visits = Column(Boolean, default=True)
    has_home_studio  = Column(Boolean, default=False)
    rating_avg       = Column(Numeric(3, 2))
    review_count     = Column(Integer, default=0)
    price_level      = Column(SmallInteger)
    is_verified      = Column(Boolean, default=False)
    is_active        = Column(Boolean, default=True)
    needs_review     = Column(Boolean, default=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio     = relationship("ProfessionalPortfolio", back_populates="professional", cascade="all,delete")
    availability  = relationship("ProfessionalAvailability", back_populates="professional", cascade="all,delete")
    social_links  = relationship("ProfessionalSocialLink", back_populates="professional", cascade="all,delete")


class ProfessionalPortfolio(Base):
    __tablename__ = "professional_portfolio"

    id              = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False)
    url_after       = Column(String(1000), nullable=False)
    url_before      = Column(String(1000))
    caption         = Column(String(255))
    service_tag     = Column(String(80))
    is_featured     = Column(Boolean, default=False)
    sort_order      = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)

    professional = relationship("Professional", back_populates="portfolio")


class ProfessionalAvailability(Base):
    __tablename__ = "professional_availability"
    __table_args__ = (UniqueConstraint("professional_id", "day_of_week"),)

    id              = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False)
    day_of_week     = Column(SmallInteger, nullable=False)
    start_time      = Column(Time)
    end_time        = Column(Time)
    is_available    = Column(Boolean, default=True)

    professional = relationship("Professional", back_populates="availability")


class ProfessionalSocialLink(Base):
    __tablename__ = "professional_social_links"
    __table_args__ = (UniqueConstraint("professional_id", "platform"),)

    id              = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey("professionals.id", ondelete="CASCADE"), nullable=False)
    platform        = Column(String(50), nullable=False)
    url             = Column(String(500), nullable=False)

    professional = relationship("Professional", back_populates="social_links")
