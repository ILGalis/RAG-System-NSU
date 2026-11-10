from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user,
    get_db,
    get_space_or_404,
    require_space_access,
    require_space_owner,
)
from app.crud import space as space_crud
from backend.models import User
from backend.schemas.space import (
    RagSpaceCreate,
    RagSpaceResponse,
    RagSpaceUpdate,
)

router = APIRouter(prefix="/spaces", tags=["spaces"])


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
    space = get_space_or_404(db, space_id)
    require_space_access(db, space, current_user)
    return space


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
    space = get_space_or_404(db, space_id)
    require_space_access(db, space, current_user)
    require_space_owner(space, current_user)
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
    space = get_space_or_404(db, space_id)
    require_space_access(db, space, current_user)
    require_space_owner(space, current_user)
    space_crud.delete_space(db, space)