"""add mime_type in document

Revision ID: f3d0f3f01f5d
Revises: 840e9e284345
Create Date: 2026-11-17 10:59:09.844625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3d0f3f01f5d'
down_revision: Union[str, Sequence[str], None] = '840e9e284345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("mime_type", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "mime_type")
