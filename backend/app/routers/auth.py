import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from slowapi import Limiter
from slowapi.util import get_remote_address
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
limiter = Limiter(key_func=get_remote_address)

COOKIE_OPTS = dict(httponly=True, samesite="lax", secure=True)

# ─────────────────────────── helpers ──────────────────────────────────────────

# Google JWKS — cached in module-level dict, refreshed when kid is missing
_google_jwks: dict = {}
_GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"


def _verify_google_id_token(id_token: str, audience: str) -> dict:
    """Verify Google id_token signature (RS256) and standard claims.

    Fetches Google JWKS on first call or when the key id (kid) is unknown.
    Raises on any verification failure — caller should treat as auth error.
    """
    import httpx
    from jose import jwt as jose_jwt, jwk, JWTError
    from jose.utils import base64url_decode
    import json as _json

    if not id_token:
        raise ValueError("empty id_token")

    # Decode header to get kid without verifying signature yet
    header_seg = id_token.split(".")[0]
    header_seg += "=" * (4 - len(header_seg) % 4)
    import base64 as _b64
    header = _json.loads(_b64.urlsafe_b64decode(header_seg))
    kid = header.get("kid")

    global _google_jwks
    if kid not in _google_jwks:
        resp = httpx.get(_GOOGLE_JWKS_URI, timeout=10)
        resp.raise_for_status()
        _google_jwks = {k["kid"]: k for k in resp.json()["keys"]}

    if kid not in _google_jwks:
        raise ValueError(f"kid {kid!r} not in Google JWKS")

    public_key = jwk.construct(_google_jwks[kid])
    claims = jose_jwt.decode(
        id_token,
        public_key,
        algorithms=["RS256"],
        audience=audience,
        issuer=["https://accounts.google.com", "accounts.google.com"],
        options={"verify_exp": True},
    )

    if not claims.get("email_verified"):
        raise ValueError("email not verified by Google")

    return claims


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
@limiter.limit("5/minute;20/hour")
async def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    _check_honeypot(body.model_dump())

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
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Invalid token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role,
            "preferred_language": user.preferred_language, "is_email_verified": user.is_email_verified,
            "avatar_url": user.avatar_url}


@router.post("/forgot-password")
@limiter.limit("3/minute;10/hour")
async def forgot_password(request: Request, body: ForgotPasswordIn, db: Session = Depends(get_db)):
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


GOOGLE_REDIRECT_URI = "https://lookla.gr/api/auth/google/callback"
GOOGLE_SCOPES = "openid email profile"


@router.get("/google/start")
async def google_start(locale: str = "el", response: Response = None):
    """Redirect browser to Google OAuth consent screen."""
    if not settings.google_client_id:
        raise HTTPException(503, "Google OAuth not configured")
    import urllib.parse
    from fastapi.responses import RedirectResponse

    csrf_token = secrets.token_urlsafe(32)
    # state = "<csrf_token>:<locale>" — validated on callback
    state = f"{csrf_token}:{locale}"
    params = urllib.parse.urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "state": state,
    })
    redirect = RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")
    # Store CSRF token in a short-lived httpOnly cookie for callback validation
    redirect.set_cookie("oauth_csrf", csrf_token, max_age=600, **COOKIE_OPTS)
    return redirect


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str = "",
    response: Response = None,
    db: Session = Depends(get_db),
    oauth_csrf: str = Cookie(default=None),
):
    """Handle Google OAuth callback, set session cookie, redirect to account."""
    from fastapi.responses import RedirectResponse

    # Parse state: "<csrf_token>:<locale>"
    parts = state.split(":", 1)
    csrf_from_state = parts[0] if parts else ""
    locale = parts[1] if len(parts) > 1 and parts[1] in ("el", "en", "ru", "uk") else "el"
    prefix = "" if locale == "el" else f"/{locale}"
    error_url = f"{prefix}/login?error=google_failed"

    # CSRF validation — reject if token missing or mismatched
    if not oauth_csrf or not secrets.compare_digest(oauth_csrf, csrf_from_state):
        return RedirectResponse(f"{prefix}/login?error=csrf_mismatch")

    if not settings.google_client_id:
        return RedirectResponse(error_url)

    async with __import__('httpx').AsyncClient() as client:
        token_r = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if not token_r.is_success:
            return RedirectResponse(error_url)

        id_token = token_r.json().get("id_token", "")
        try:
            userinfo = _verify_google_id_token(id_token, settings.google_client_id)
        except Exception:
            return RedirectResponse(error_url)

    google_id = userinfo.get("sub")
    email     = userinfo.get("email")
    name      = userinfo.get("name", "")

    if not google_id or not email:
        return RedirectResponse(error_url)

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(email=email, name=name, google_id=google_id, is_email_verified=True,
                        preferred_language=locale)
            db.add(user)
            db.flush()
    db.commit()

    redirect = RedirectResponse(f"{prefix}/account", status_code=302)
    _set_auth_cookies(redirect, user.id)
    redirect.delete_cookie("oauth_csrf")
    return redirect
