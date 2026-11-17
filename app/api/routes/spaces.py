from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.error import AppError
import shutil
from pathlib import Path
from sqlalchemy import select
from backend.models import Document
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
    if data.access_mode == "public" and current_user.role != "teacher":
        raise AppError(403, "public_requires_teacher", "Публичные пространства создают только преподаватели")
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
    if data.access_mode == "public" and current_user.role != "teacher":
        raise AppError(
            403,
            "public_requires_teacher",
            "Публичные пространства создают только преподаватели",
        )
    return space_crud.update_space(db, space, data)


""" @router.delete(
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
"""
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

    file_paths = db.scalars(
        select(Document.file_path).where(Document.space_id == space_id)
    ).all()

    space_crud.delete_space(db, space)

    for path in file_paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass

    space_dir = Path("storage/spaces") / str(space_id)
    if space_dir.exists():
        shutil.rmtree(space_dir, ignore_errors=True)