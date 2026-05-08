"""company_branches, company_branch_contacts, company_branch_working_hours.

Revision ID: 027
Revises: 026
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_branches",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_name", sa.String(512), nullable=False),
        sa.Column("branch_location_description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(11, 8), nullable=True),
        sa.Column("branch_type", sa.String(32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_visible_to_clients", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "branch_type IN ('factory', 'warehouse', 'showroom', 'office')",
            name="ck_company_branches_branch_type",
        ),
        sa.CheckConstraint(
            "(latitude IS NULL AND longitude IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL)",
            name="ck_company_branches_lat_lon_pair",
        ),
    )
    op.create_index("ix_company_branches_company_id", "company_branches", ["company_id"], unique=False)
    op.create_index("ix_company_branches_branch_type", "company_branches", ["branch_type"], unique=False)
    op.create_index("ix_company_branches_is_active", "company_branches", ["is_active"], unique=False)
    op.create_index(
        "ix_company_branches_is_visible_to_clients",
        "company_branches",
        ["is_visible_to_clients"],
        unique=False,
    )

    op.create_table(
        "company_branch_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("contact_name", sa.String(256), nullable=False),
        sa.Column("phone_number", sa.String(64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["company_branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_branch_contacts_branch_id",
        "company_branch_contacts",
        ["branch_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_branch_contacts_is_active",
        "company_branch_contacts",
        ["is_active"],
        unique=False,
    )
    op.create_index(
        "uq_company_branch_contacts_one_primary_active",
        "company_branch_contacts",
        ["branch_id"],
        unique=True,
        postgresql_where=sa.text("is_primary IS TRUE AND is_active IS TRUE"),
    )

    op.create_table(
        "company_branch_working_hours",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("day_of_week", sa.String(16), nullable=False),
        sa.Column("is_day_off", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("opening_time", sa.Time(), nullable=True),
        sa.Column("closing_time", sa.Time(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["company_branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "day_of_week IN ("
            "'saturday', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday'"
            ")",
            name="ck_company_branch_working_hours_day",
        ),
        sa.CheckConstraint(
            "(is_day_off = true AND opening_time IS NULL AND closing_time IS NULL) "
            "OR (is_day_off = false AND opening_time IS NOT NULL AND closing_time IS NOT NULL "
            "AND closing_time > opening_time)",
            name="ck_company_branch_working_hours_times",
        ),
        sa.UniqueConstraint("branch_id", "day_of_week", name="uq_company_branch_working_hours_branch_day"),
    )
    op.create_index(
        "ix_company_branch_working_hours_branch_id",
        "company_branch_working_hours",
        ["branch_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_branch_working_hours_day_of_week",
        "company_branch_working_hours",
        ["day_of_week"],
        unique=False,
    )
    op.create_index(
        "ix_company_branch_working_hours_is_active",
        "company_branch_working_hours",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_company_branch_working_hours_is_active", table_name="company_branch_working_hours")
    op.drop_index("ix_company_branch_working_hours_day_of_week", table_name="company_branch_working_hours")
    op.drop_index("ix_company_branch_working_hours_branch_id", table_name="company_branch_working_hours")
    op.drop_table("company_branch_working_hours")

    op.drop_index("uq_company_branch_contacts_one_primary_active", table_name="company_branch_contacts")
    op.drop_index("ix_company_branch_contacts_is_active", table_name="company_branch_contacts")
    op.drop_index("ix_company_branch_contacts_branch_id", table_name="company_branch_contacts")
    op.drop_table("company_branch_contacts")

    op.drop_index("ix_company_branches_is_visible_to_clients", table_name="company_branches")
    op.drop_index("ix_company_branches_is_active", table_name="company_branches")
    op.drop_index("ix_company_branches_branch_type", table_name="company_branches")
    op.drop_index("ix_company_branches_company_id", table_name="company_branches")
    op.drop_table("company_branches")
