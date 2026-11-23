import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_space_or_404, require_space_owner
from app.core.error import AppError
from backend.models import Invitation, SpaceMember, User
from backend.schemas.invitation import (
    AcceptInvitationRequest, InvitationCreate,
    InvitationCreatedResponse, InvitationResponse,
)

router = APIRouter(tags=["invitations"])

def _hash_code(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def invitation_status(inv: Invitation, now: datetime) -> str:
    if inv.used_at is not None:
        return "used"
    if inv.revoked_at is not None:
        return "revoked"
    if inv.expires_at < now:
        return "expired"
    return "active"


@router.post("/spaces/{space_id}/invitations", response_model=InvitationCreatedResponse, status_code=201)
def create_invitation(
    space_id: int,
    data: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    raw_code = secrets.token_urlsafe(8)
    inv = Invitation(
        space_id=space_id,
        created_by=current_user.id,
        code_hash=_hash_code(raw_code),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=data.ttl_hours),
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    return InvitationCreatedResponse(
        id=inv.id, space_id=inv.space_id, status="active",
        expires_at=inv.expires_at, created_at=inv.created_at,
        used_at=None, used_by=None, code=raw_code
    )


@router.get("/spaces/{space_id}/invitations", response_model=list[InvitationResponse])
def list_invitations(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    invs = db.scalars(select(Invitation).where(Invitation.space_id == space_id)).all()
    now = datetime.now(timezone.utc)

    
    return [
        InvitationResponse(
            id=i.id, space_id=i.space_id, status=invitation_status(i, now),
            expires_at=i.expires_at, created_at=i.created_at,
            used_at=i.used_at, used_by=i.used_by
        )
        for i in invs
    ]


@router.delete("/spaces/{space_id}/invitations/{inv_id}", status_code=204)
def revoke_invitation(
    space_id: int,
    inv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    inv = db.get(Invitation, inv_id)
    if not inv or inv.space_id != space_id:
        raise AppError(404, "invitation_not_found", "Приглашение не найдено")

    if inv.used_at or inv.revoked_at:
        return  # уже использовано или отозвано, ничего не делаем

    inv.revoked_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/invitations/accept")
def accept_invitation(
    data: AcceptInvitationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.scalar(
        select(Invitation).where(Invitation.code_hash == _hash_code(data.code)).with_for_update()
    )
    
    now = datetime.now(timezone.utc)
    if not inv or invitation_status(inv, now) != "active":
        raise AppError(400, "invalid_invitation", "Код недействителен, истёк или отозван")

    if inv.space_id: # Если пространства уже нет (каскад)
        pass # (на деле каскад удалит и инвайт, но на всякий)

    # Проверяем, нет ли уже в пространстве
    member = db.scalar(
        select(SpaceMember).where(
            SpaceMember.space_id == inv.space_id,
            SpaceMember.user_id == current_user.id,
        )
    )
    if member:
        raise AppError(409, "already_member", "Вы уже являетесь участником")

    # Добавляем
    new_member = SpaceMember(
        space_id=inv.space_id,
        user_id=current_user.id,
        role="student",
    )
    db.add(new_member)

    inv.used_at = now
    inv.used_by = current_user.id
    db.commit()

    return {"status": "joined", "space_id": str(inv.space_id)}