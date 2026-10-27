from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.error import AppError
from app.crud import space as space_crud
from backend.schemas.space import (
    RagSpaceCreate,
    RagSpaceResponse,
    RagSpaceUpdate,
)

router = APIRouter(
    prefix="/spaces",
    tags=["spaces"],
)


@router.post(
    "",
    response_model=RagSpaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_space(
    data: RagSpaceCreate,
    db: Session = Depends(get_db),
) -> RagSpaceResponse:
    space = space_crud.create_space(
        db,
        data,
    )
    return space


@router.get(
    "",
    response_model=list[RagSpaceResponse],
)
def list_spaces(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[RagSpaceResponse]:
    return space_crud.list_spaces_for_user(
        db,
        user_id,
    )


@router.get(
    "/{space_id}",
    response_model=RagSpaceResponse,
)
def get_space(
    space_id: int,
    db: Session = Depends(get_db),
) -> RagSpaceResponse:
    space = space_crud.get_space(
        db,
        space_id,
    )
    if space is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="space_not_found",
            message=f"Space {space_id} not found",
        )
    return space


@router.patch(
    "/{space_id}",
    response_model=RagSpaceResponse,
)
def update_space(
    space_id: int,
    data: RagSpaceUpdate,
    db: Session = Depends(get_db),
) -> RagSpaceResponse:
    space = space_crud.get_space(
        db,
        space_id,
    )
    if space is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="space_not_found",
            message=f"Space {space_id} not found",
        )
    return space_crud.update_space(
        db,
        space,
        data,
    )


@router.delete(
    "/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_space(
    space_id: int,
    db: Session = Depends(get_db),
) -> None:
    space = space_crud.get_space(
        db,
        space_id,
    )
    if space is None:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            code="space_not_found",
            message=f"Space {space_id} not found",
        )
    space_crud.delete_space(
        db,
        space,
    )