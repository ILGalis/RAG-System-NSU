from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    __table_args__ = (
        CheckConstraint(
            "file_type IN ('pdf', 'docx', 'txt')",
            name="ck_documents_file_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed')",
            name="ck_documents_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    space_id: Mapped[int] = mapped_column(
        ForeignKey("rag_spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_name: Mapped[str] = mapped_column(String(500), nullable=False)

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    file_type: Mapped[str] = mapped_column(String(10), nullable=False)

    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    error_message: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )