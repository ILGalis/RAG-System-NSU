import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.ids import document_id_str, space_id_str
from app.services.qdrant_cleanup import delete_document_points, delete_space_points
from app.api.deps import get_current_user, get_db
from app.core.error import AppError
from backend.core.security import hash_password, verify_password
from backend.core.roles import resolve_role
from backend.models import User, Document,RagSpace
from backend.models.email_token import EmailVerificationToken
from backend.models.session import Session as UserSession
from backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserOut,
    VerifyEmailRequest,
    DeleteAccountRequest,
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

    raw_token = secrets.token_urlsafe(4)
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + TOKEN_TTL,
        )
    )
    db.commit()
    #
    # TODO: заменить на реальную отправку письма через бота
    # 16.11 осталось подключить сюда бота + проверить
    # бот лежит в backend/core/email_verificator_bot.py
    logger.info("[EMAIL VERIFICATION] %s: token=%s", email, raw_token)
    print(f"[EMAIL VERIFICATION] {email}: code={raw_token}")
    #
    #
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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    data: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(data.password, current_user.password_hash):
        raise AppError(401, "invalid_password", "Неверный пароль")
    # спорный момент, если челик удалил акк а потом вернется, то у него все
    # заново придется делать, думаю пометить его в бд как удаленного
    # типо флаг добавить какой-нибудь. после новой регистрации
    # тогда флаг позволяет обойти ошибку "пользователь уже зареган"
    # cтоит написать в UI: «Все ваши пространства и документы будут безвозвратно удалены».
    # пока раз пользователь удаляет акк, сразу подчищу всё что он сделал
    # что удалим каскадом в БД:
    #   sessions, email_verification_tokens  - user_id CASCADE
    #   space_members                        - user_id CASCADE
    #   rag_spaces (свои)                    - owner_id CASCADE
    #   documents                            - space_id + uploaded_by CASCADE
    #
    # Файлы на диске каскадом не удаляются => собераем путь заранее

    file_paths = db.scalars(
        select(Document.file_path).where(Document.uploaded_by == current_user.id)
    ).all()

    space_ids = db.scalars(
        select(RagSpace.id).where(RagSpace.owner_id == current_user.id)
    ).all()
    own_space_ids = list(space_ids)
    foreign_docs = db.execute(
        select(Document.space_id, Document.id).where(
            Document.uploaded_by == current_user.id,
            Document.space_id.notin_(own_space_ids) if own_space_ids else True,
        )
    ).all()
    db.delete(current_user)
    db.commit()

    # Best-effort очистка диска — БД уже консистентна.
    for path in file_paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

    for sid in space_ids:
        space_dir = Path("storage/spaces") / str(sid)
        if space_dir.exists():
            shutil.rmtree(space_dir, ignore_errors=True)
    for sid in own_space_ids:
        delete_space_points(space_id_str(sid))

    for f_space_id, f_doc_id in foreign_docs:
        delete_document_points(space_id_str(f_space_id), document_id_str(f_doc_id))