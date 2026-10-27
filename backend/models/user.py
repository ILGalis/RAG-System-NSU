from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    func,
    Boolean ,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column


from backend.db.base import Base

class User(Base):
    __tablename__="users"
    
    __table_args__ = (
        CheckConstraint("role IN ('teacher', 'student')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

