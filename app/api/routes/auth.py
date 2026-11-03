import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.error import AppError
from backend.core.security import hash_password, verify_password
from backend.core.roles import resolve_role
from backend.models import User
from backend.models.email_token import EmailVerificationToken
from backend.models.session import Session as UserSession
from backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserOut,
    VerifyEmailRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

NSU_DOMAIN_RE = re.compile(r"^([a-z0-9-]+\.)*nsu\.ru$", re.IGNORECASE)
TOKEN_TTL = timedelta(hours=24)
SESSION_TTL = timedelta(days=7)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    email = data.email.strip().lower()
    domain = email.split("@", 1)[1]
    if not NSU_DOMAIN_RE.match(domain):
        raise AppError(
            400,
            "invalid_domain",
            "Регистрация доступна только для почты НГУ",
        )

    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise AppError(
            409,
            "email_taken",
            "Пользователь с такой почтой уже существует",
        )

    user = User(
        email=email,
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        password_hash=hash_password(data.password),
        role="student",
        is_email_verified=False,
    )
    db.add(user)
    db.flush()

    raw_token = secrets.token_urlsafe(32)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
        )
    )
    db.commit()

    # TODO: заменить на реальную отправку письма через почтовый сервис.
    logger.info("[EMAIL VERIFICATION] %s: token=%s", email, raw_token)

    return {
        "status": "pending_verification",
        "message": "Проверьте почту",
    }


@router.post("/verify-email")
def verify_email(
    data: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> dict:
    token_hash = _hash_token(data.token)
    record = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash
        )
    )
    now = datetime.now(timezone.utc)

    if record is None or record.used_at is not None or record.expires_at < now:
        raise AppError(400, "invalid_token", "Токен недействителен или истёк")

    user = db.get(User, record.user_id)
    if user is None:
        raise AppError(400, "invalid_token", "Пользователь не найден")

    user.is_email_verified = True
    record.used_at = now
    db.commit()

    return {"status": "verified"}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)) -> dict:
    email = data.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(data.password, user.password_hash):
        raise AppError(401, "invalid_credentials", "Неверная почта или пароль")

    if not user.is_email_verified:
        raise AppError(
            403,
            "email_not_verified",
            "Подтвердите почту перед входом",
        )
    user.role = resolve_role(user.email)
    #db.commit()
    raw_token = secrets.token_urlsafe(32)
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + SESSION_TTL,
        )
    )
    db.commit()

    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user).model_dump(),
    }


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)