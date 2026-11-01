from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.error import AppError
from app.crud import space as space_crud
from backend.models import RagSpace, SpaceMember, User
from backend.schemas.space import (
    RagSpaceCreate,
    RagSpaceResponse,
    RagSpaceUpdate,
)

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"],
)

#переделан user id, теперь нельзя просто так достать, берем из токена
def _get_accessible_space(
    db: Session,
    space_id: int,
    user: User,
) -> RagSpace:
    space = space_crud.get_space(db, space_id)
    if space is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="space_not_found",
            message=f"Space {space_id} not found",
        )

    is_owner = space.owner_id == user.id
    is_member = db.scalar(
        select(SpaceMember.id).where(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user.id,
        )
    ) is not None

    if not (is_owner or is_member or space.access_mode == "public"):
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="access_denied",
            message="Нет доступа к пространству",
        )

    return space


def _require_owner(
    db: Session,
    space: RagSpace,
    user: User,
) -> None:
    if space.owner_id != user.id:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            code="not_owner",
            message="Только владелец может изменять пространство",
        )


@router.post(
    "",
    response_model=RagSpaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_space(
    data: RagSpaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagSpaceResponse:
    # owner_id берём из токена
    data = data.model_copy(update={"owner_id": current_user.id})
    return space_crud.create_space(db, data)


@router.get(
    "",
    response_model=list[RagSpaceResponse],
)
def list_spaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RagSpaceResponse]:
    return space_crud.list_spaces_for_user(db, current_user.id)


@router.get(
    "/{space_id}",
    response_model=RagSpaceResponse,
)
def get_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagSpaceResponse:
    return _get_accessible_space(db, space_id, current_user)


@router.patch(
    "/{space_id}",
    response_model=RagSpaceResponse,
)
def update_space(
    space_id: int,
    data: RagSpaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagSpaceResponse:
    space = _get_accessible_space(db, space_id, current_user)
    _require_owner(db, space, current_user)
    return space_crud.update_space(db, space, data)


@router.delete(
    "/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_space(
    space_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    space = _get_accessible_space(db, space_id, current_user)
    _require_owner(db, space, current_user)
    space_crud.delete_space(db, space)