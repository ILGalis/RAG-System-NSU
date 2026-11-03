"""add user first and last name

Revision ID: 46963d726079
Revises: 7e6909083208
Create Date: 2026-11-03 21:29:29.192084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46963d726079'
down_revision: Union[str, Sequence[str], None] = '7e6909083208'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("first_name", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("last_name", sa.String(length=100), nullable=True),
    )

    op.execute("UPDATE users SET first_name = '' WHERE first_name IS NULL")
    op.execute("UPDATE users SET last_name = '' WHERE last_name IS NULL")

    op.alter_column(
        "users",
        "first_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        "users",
        "last_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
