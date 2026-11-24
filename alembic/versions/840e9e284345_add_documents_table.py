"""add documents table

Revision ID: 840e9e284345
Revises: 3cfa5645947e
Create Date: 2026-11-16 21:21:58.311728

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '840e9e284345'
down_revision: str | Sequence[str] | None = '3cfa5645947e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('space_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='pending',
            nullable=False,
        ),
        sa.Column('error_message', sa.String(length=2000), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            "file_type IN ('pdf', 'docx', 'txt')",
            name='ck_documents_file_type',
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'ready', 'failed')",
            name='ck_documents_status',
        ),
        sa.ForeignKeyConstraint(['space_id'], ['rag_spaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_space_id'), 'documents', ['space_id'], unique=False)
    op.create_index(op.f('ix_documents_uploaded_by'), 'documents', ['uploaded_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_uploaded_by'), table_name='documents')
    op.drop_index(op.f('ix_documents_space_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
