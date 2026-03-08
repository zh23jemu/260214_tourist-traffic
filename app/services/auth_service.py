import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_ROLE,
    DEFAULT_ADMIN_USERNAME,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
)
from app.database import get_db
from app.models import UserAccount

bearer_scheme = HTTPBearer(auto_error=False)


def _pbkdf2_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = password_hash.split("$", 1)
    except ValueError:
        return False
    expected = base64.b64decode(digest_b64.encode())
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        base64.b64decode(salt_b64.encode()),
        100_000,
    )
    return hmac.compare_digest(actual_hash, expected)


def hash_password(password: str) -> str:
    return _pbkdf2_hash(password=password)


def create_access_token(user: UserAccount) -> tuple[str, int]:
    expires_delta = timedelta(minutes=JWT_EXPIRE_MINUTES)
    expires_at = datetime.now(UTC) + expires_delta
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": expires_at,
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, int(expires_delta.total_seconds())


def authenticate_user(db: Session, username: str, password: str) -> UserAccount | None:
    user = db.execute(select(UserAccount).where(UserAccount.username == username)).scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    if not verify_password(password=password, password_hash=user.password_hash):
        return None
    return user


def ensure_default_admin(db: Session) -> None:
    existing = db.execute(select(UserAccount).where(UserAccount.username == DEFAULT_ADMIN_USERNAME)).scalar_one_or_none()
    if existing is not None:
        return
    db.add(
        UserAccount(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=DEFAULT_ADMIN_ROLE,
            is_active=True,
        )
    )
    db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserAccount:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token subject")

    user = db.execute(select(UserAccount).where(UserAccount.username == username)).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found or inactive")
    return user
