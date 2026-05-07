"""Company documents/files + documents_media.

Revision ID: 023
Revises: 022
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_documents_and_files",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("reminder_by_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "document_type IN ("
            "'document', 'commercial_registration', 'tax_card', 'operation_license', "
            "'lease_contract', 'industrial_registration', 'contract', 'other'"
            ")",
            name="ck_company_documents_and_files_document_type",
        ),
        sa.CheckConstraint(
            "reminder_by_days IS NULL OR reminder_by_days >= 0",
            name="ck_company_documents_and_files_reminder_by_days",
        ),
    )
    op.create_index(
        "ix_company_documents_and_files_company_id",
        "company_documents_and_files",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_documents_and_files_document_type",
        "company_documents_and_files",
        ["document_type"],
        unique=False,
    )

    op.create_table(
        "documents_media",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_document_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("media_type", sa.String(16), nullable=False),
        sa.Column("media_link", sa.String(2048), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_document_id"],
            ["company_documents_and_files.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "media_type IN ('images', 'videos', 'files')",
            name="ck_documents_media_media_type",
        ),
    )
    op.create_index(
        "ix_documents_media_company_document_id",
        "documents_media",
        ["company_document_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_documents_media_company_document_id", table_name="documents_media")
    op.drop_table("documents_media")
    op.drop_index("ix_company_documents_and_files_document_type", table_name="company_documents_and_files")
    op.drop_index("ix_company_documents_and_files_company_id", table_name="company_documents_and_files")
    op.drop_table("company_documents_and_files")
