from datetime import datetime, timezone
from collections.abc import Generator
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.error import AppError
from backend.db.connection import SessionLocal
from backend.models import User
from backend.models.session import Session as UserSession


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_token(raw: str) -> str:
    import hashlib
    return hashlib.sha256(raw.encode()).hexdigest()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(401, "not_authenticated", "Требуется авторизация")

    raw_token = authorization.removeprefix("Bearer ").strip()
    session = db.scalar(
        select(UserSession).where(UserSession.token_hash == _hash_token(raw_token))
    )

    if session is None or session.expires_at < datetime.now(timezone.utc):
        raise AppError(401, "invalid_session", "Сессия недействительна или истекла")

    user = db.get(User, session.user_id)
    if user is None:
        raise AppError(401, "invalid_session", "Пользователь не найден")

    return user