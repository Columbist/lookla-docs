from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt as _bcrypt
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "access"}, settings.secret_key, ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "refresh"}, settings.secret_key, ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def generate_readable_password() -> str:
    import secrets
    vowels = "aeiou"
    consonants = "bcdfghjkmnpqrstvwxyz"
    digits = "23456789"
    parts = [secrets.choice(consonants if i % 2 == 0 else vowels) for i in range(8)]
    parts += [secrets.choice(digits), secrets.choice(digits)]
    return "".join(parts)
