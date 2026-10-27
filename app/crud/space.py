from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.orm import Session

from backend.models import (
    RagSpace,
    SpaceMember,
)
from backend.schemas.space import (
    RagSpaceCreate,
    RagSpaceUpdate,
)


def create_space(
    db: Session,
    data: RagSpaceCreate,
) -> RagSpace:
    space = RagSpace(
        name=data.name,
        owner_id=data.owner_id,
        access_mode=data.access_mode,
    )
    db.add(space)
    db.flush()

    member = SpaceMember(
        space_id=space.id,
        user_id=data.owner_id,
        role="owner",
    )
    db.add(member)

    db.commit()
    db.refresh(space)

    return space


def get_space(
    db: Session,
    space_id: int,
) -> RagSpace | None:
    return db.scalar(
        select(RagSpace).where(
            RagSpace.id == space_id,
        )
    )


def list_spaces_for_user(
    db: Session,
    user_id: int,
) -> list[RagSpace]:
    stmt = (
        select(RagSpace)
        .outerjoin(
            SpaceMember,
            SpaceMember.space_id == RagSpace.id,
        )
        .where(
            or_(
                RagSpace.owner_id == user_id,
                SpaceMember.user_id == user_id,
                RagSpace.access_mode == "public",
            )
        )
        .distinct()
    )
    return list(db.scalars(stmt).all())


def update_space(
    db: Session,
    space: RagSpace,
    data: RagSpaceUpdate,
) -> RagSpace:
    payload = data.model_dump(
        exclude_unset=True,
    )
    for field, value in payload.items():
        setattr(space, field, value)

    db.commit()
    db.refresh(space)

    return space


def delete_space(
    db: Session,
    space: RagSpace,
) -> None:
    db.delete(space)
    db.commit()