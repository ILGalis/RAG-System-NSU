from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import  Mapped, mapped_column, relationship

from app.db.base import Base

class RagSpace(Base):
    __tablename__ = "rag_spaces"

    __table_args__ = (
        CheckConstraint(
            "access_mode IN ('private', 'public')",
            name="ck_rag_spaces_access_mode",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    access_mode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="private",
        server_default="private",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    members: Mapped[list["SpaceMember"]] = relationship(
        back_populates="space",
        cascade="all, delete-orphan",
    )

class SpaceMember(Base):
    __tablename__ = "space_members"

    __table_args__ = (
        UniqueConstraint(
            "space_id",
            "user_id",
            name="uq_space_members_space_user",
        ),
        CheckConstraint(
            "role IN ('owner', 'teacher', 'student')",
            name="ck_space_members_role",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    space_id: Mapped[int] = mapped_column(
        ForeignKey(
            "rag_spaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
        server_default="student",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    space: Mapped["RagSpace"] = relationship(
        back_populates="members",
    )