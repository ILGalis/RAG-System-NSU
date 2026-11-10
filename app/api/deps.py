import hashlib
from collections.abc import Callable, Generator
from datetime import datetime, timezone

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.error import AppError
from backend.db.connection import SessionLocal
from backend.models import RagSpace, SpaceMember, User
from backend.models.session import Session as UserSession


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_token(raw: str) -> str:
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


def require_role(*roles: str) -> Callable[..., User]:
    """Dependency-фабрика: пускает только пользователей с одной из ролей."""
    allowed = frozenset(roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise AppError(
                403,
                "forbidden",
                f"Требуется одна из ролей: {', '.join(sorted(allowed))}",
            )
        return current_user

    return _checker


def get_space_or_404(db: Session, space_id: int) -> RagSpace:
    space = db.get(RagSpace, space_id)
    if space is None:
        raise AppError(
            404,
            "space_not_found",
            f"Space {space_id} not found",
        )
    return space


def _is_space_member(db: Session, space_id: int, user_id: int) -> bool:
    return db.scalar(
        select(SpaceMember.id).where(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user_id,
        )
    ) is not None


def require_space_access(
    db: Session,
    space: RagSpace,
    user: User,
) -> RagSpace:
    """Пускает владельца, участника или любого авторизованного для public."""
    if (
        space.owner_id == user.id
        or space.access_mode == "public"
        or _is_space_member(db, space.id, user.id)
    ):
        return space
    raise AppError(403, "access_denied", "Нет доступа к пространству")


def require_space_owner(space: RagSpace, user: User) -> None:
    if space.owner_id != user.id:
        raise AppError(
            403,
            "not_owner",
            "Только владелец может изменять пространство",
        )