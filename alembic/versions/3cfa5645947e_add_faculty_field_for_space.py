"""add faculty field for space

Revision ID: 3cfa5645947e
Revises: 46963d726079
Create Date: 2026-11-16 21:13:08.214220

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3cfa5645947e'
down_revision: str | Sequence[str] | None = '46963d726079'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rag_spaces",
        sa.Column(
            "faculty",
            sa.String(length=200),
            nullable = False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("rag_spaces", "faculty")
