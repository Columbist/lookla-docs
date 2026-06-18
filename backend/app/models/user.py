from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id                 = Column(Integer, primary_key=True)
    email              = Column(String(255), unique=True, nullable=False)
    password_hash      = Column(String(255))
    name               = Column(String(255))
    phone              = Column(String(30))
    viber_phone        = Column(String(30))
    whatsapp_phone     = Column(String(30))
    avatar_url         = Column(String(500))
    role               = Column(String(30), default="user")   # user | salon_owner | admin
    preferred_language = Column(String(2), default="el")
    is_active          = Column(Boolean, default=True)
    is_email_verified  = Column(Boolean, default=False)
    google_id          = Column(String(100), unique=True)
    apple_id           = Column(String(100), unique=True)
    created_at         = Column(DateTime, default=datetime.utcnow)


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False)
    token      = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at    = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False)
    token      = Column(String(64), unique=True, nullable=False)
    channel    = Column(String(20), default="email")   # email | whatsapp | sms
    expires_at = Column(DateTime, nullable=False)
    used_at    = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
