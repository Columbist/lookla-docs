import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_readable_password,
)
from app.core.config import get_settings
from app.models.user import User, EmailVerification, RefreshToken
from app.services.email import send_email
from app.services.moderation import is_disposable_email

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

COOKIE_OPTS = dict(httponly=True, samesite="lax", secure=False)  # secure=True after HTTPS

# ─────────────────────────── helpers ──────────────────────────────────────────

def _set_auth_cookies(response: Response, user_id: int):
    access  = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    response.set_cookie("access_token",  access,  max_age=60 * settings.access_token_expire_minutes,  **COOKIE_OPTS)
    response.set_cookie("refresh_token", refresh, max_age=60 * 60 * 24 * settings.refresh_token_expire_days, **COOKIE_OPTS)
    return access, refresh


def _store_refresh(db: Session, user_id: int, token: str):
    payload = decode_token(token)
    h = hashlib.sha256(token.encode()).hexdigest()
    db.execute(text("""
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
        VALUES (:uid, :h, :exp)
    """), {"uid": user_id, "h": h, "exp": datetime.fromtimestamp(payload["exp"], tz=timezone.utc)})


def _check_honeypot(body: dict):
    if body.get("website_url"):  # hidden field — bots fill it
        raise HTTPException(400, "Invalid request")


# ─────────────────────────── schemas ──────────────────────────────────────────

class RegisterIn(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    name: Optional[str] = None
    preferred_language: str = "el"
    website_url: str = ""          # honeypot — should be empty

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordIn(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    channel: str = "email"   # email | whatsapp | sms

class ResetPasswordIn(BaseModel):
    token: str
    new_password: str

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


# ─────────────────────────── endpoints ────────────────────────────────────────

@router.post("/register", status_code=201)
async def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    _check_honeypot(body.dict())

    if is_disposable_email(body.email):
        raise HTTPException(400, "Disposable email addresses are not allowed")

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(409, "Email already registered")

    # Use provided password or generate one
    raw_password = body.password or generate_readable_password()
    generated = not body.password

    user = User(
        email=body.email,
        password_hash=hash_password(raw_password),
        name=body.name,
        preferred_language=body.preferred_language,
        is_email_verified=False,
    )
    db.add(user)
    db.flush()  # get user.id

    # Email verification token
    token = secrets.token_urlsafe(32)
    ev = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(ev)
    db.commit()

    verify_url = f"https://lookla.gr/verify-email?token={token}"
    await send_email(body.email, "verify", lang=body.preferred_language, url=verify_url)

    _set_auth_cookies(response, user.id)

    return {
        "id": user.id,
        "email": user.email,
        "is_email_verified": False,
        **({"generated_password": raw_password} if generated else {}),
    }


@router.post("/generate-password")
def gen_password():
    return {"password": generate_readable_password()}


@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    ev = db.query(EmailVerification).filter(
        EmailVerification.token == token,
        EmailVerification.used_at == None,
        EmailVerification.expires_at > datetime.now(timezone.utc),
    ).first()
    if not ev:
        raise HTTPException(400, "Invalid or expired token")

    ev.used_at = datetime.now(timezone.utc)
    db.execute(text("UPDATE users SET is_email_verified = true WHERE id = :id"), {"id": ev.user_id})
    db.commit()
    return {"status": "ok"}


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")

    access, refresh = _set_auth_cookies(response, user.id)
    _store_refresh(db, user.id, refresh)
    db.commit()

    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "preferred_language": user.preferred_language}


@router.post("/logout")
def logout(response: Response, refresh_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if refresh_token:
        h = hashlib.sha256(refresh_token.encode()).hexdigest()
        db.execute(text("UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = :h"), {"h": h})
        db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"status": "ok"}


@router.post("/refresh")
def refresh_token(response: Response, refresh_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(401, "No refresh token")
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")

    h = hashlib.sha256(refresh_token.encode()).hexdigest()
    stored = db.execute(text("""
        SELECT id FROM refresh_tokens
        WHERE token_hash = :h AND revoked_at IS NULL AND expires_at > NOW()
    """), {"h": h}).first()
    if not stored:
        raise HTTPException(401, "Token revoked or expired")

    user_id = int(payload["sub"])
    access, new_refresh = _set_auth_cookies(response, user_id)
    # Rotate: revoke old, store new
    db.execute(text("UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = :h"), {"h": h})
    _store_refresh(db, user_id, new_refresh)
    db.commit()
    return {"status": "ok"}


@router.get("/me")
def get_me(access_token: Optional[str] = Cookie(None), db: Session = Depends(get_db)):
    if not access_token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(access_token)
    if not payload:
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role,
            "preferred_language": user.preferred_language, "is_email_verified": user.is_email_verified,
            "avatar_url": user.avatar_url}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    user = None
    if body.email:
        user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    if not user:
        # Don't reveal if email exists
        return {"status": "ok", "message": "If this account exists, you will receive a reset link"}

    code = secrets.token_hex(3).upper()  # 6-char hex code e.g. "A3F9C1"
    token = secrets.token_urlsafe(32)

    db.execute(text("""
        INSERT INTO password_resets (user_id, token, channel, expires_at)
        VALUES (:uid, :token, :channel, NOW() + INTERVAL '10 minutes')
    """), {"uid": user.id, "token": token, "channel": body.channel})
    db.commit()

    if body.channel == "email":
        reset_url = f"https://lookla.gr/reset-password?token={token}"
        await send_email(user.email, "reset", lang=user.preferred_language, code=reset_url)
    # WhatsApp/SMS: would send OTP code — requires Meta/Brevo API key

    return {"status": "ok"}


@router.post("/reset-password")
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    reset = db.execute(text("""
        SELECT user_id FROM password_resets
        WHERE token = :token AND used_at IS NULL AND expires_at > NOW()
    """), {"token": body.token}).first()
    if not reset:
        raise HTTPException(400, "Invalid or expired reset token")

    if len(body.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    db.execute(text("UPDATE users SET password_hash = :h WHERE id = :id"),
               {"h": hash_password(body.new_password), "id": reset.user_id})
    db.execute(text("UPDATE password_resets SET used_at = NOW() WHERE token = :t"), {"t": body.token})
    db.commit()
    return {"status": "ok"}


@router.post("/google")
async def google_auth(code: str, response: Response, db: Session = Depends(get_db)):
    """Exchange Google OAuth code for user session."""
    if not settings.google_client_id:
        raise HTTPException(503, "Google OAuth not configured")

    async with __import__('httpx').AsyncClient() as client:
        # Exchange code for tokens
        token_r = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": "https://lookla.gr/auth/google/callback",
            "grant_type": "authorization_code",
        })
        if not token_r.is_success:
            raise HTTPException(400, "Google OAuth failed")

        id_token = token_r.json().get("id_token")
        # Verify and decode id_token (simplified — in prod use google-auth library)
        import base64, json
        payload_b64 = id_token.split(".")[1] + "=="
        userinfo = json.loads(base64.urlsafe_b64decode(payload_b64))

    google_id = userinfo.get("sub")
    email     = userinfo.get("email")
    name      = userinfo.get("name")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(email=email, name=name, google_id=google_id, is_email_verified=True)
            db.add(user)
            db.flush()
    db.commit()

    _set_auth_cookies(response, user.id)
    return {"id": user.id, "email": user.email, "name": user.name}
