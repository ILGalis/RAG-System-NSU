from datetime import datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    get_space_or_404,
    require_space_member,
    require_space_owner,
)
from app.core.error import AppError
from backend.models import SpaceMember, User

router = APIRouter(tags=["members"])


class SpaceMemberOut(BaseModel):
    user_id: int
    email: str
    first_name: str
    last_name: str
    role: str
    joined_at: datetime


@router.get("/spaces/{space_id}/members", response_model=list[SpaceMemberOut])
def list_members(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    space = get_space_or_404(db, space_id)
    require_space_member(db, space, current_user)  # только свои

    # Достаем участников + инфу о юзерах
    stmt = (
        select(SpaceMember, User)
        .join(User, SpaceMember.user_id == User.id)
        .where(SpaceMember.space_id == space_id)
    )
    results = db.execute(stmt).all()

    return [
        SpaceMemberOut(
            user_id=m.user_id, email=u.email,
            first_name=u.first_name, last_name=u.last_name,
            role=m.role, joined_at=m.joined_at
        )
        for m, u in results
    ]


@router.delete("/spaces/{space_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    space_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    space = get_space_or_404(db, space_id)
    require_space_owner(space, current_user)

    if user_id == space.owner_id:
        raise AppError(403, "cannot_remove_owner", "Нельзя удалить владельца пространства")

    member = db.scalar(
        select(SpaceMember).where(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user_id,
        )
    )
    if not member:
        raise AppError(404, "member_not_found", "Участник не найден")

    db.delete(member)
    db.commit()