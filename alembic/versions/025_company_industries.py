"""Company ↔ industries association (many-to-many).

Revision ID: 025
Revises: 024
Create Date: 2026-05-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "025"
down_revision: Union[str, None] = "024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_industries",
        sa.Column("company_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("industry_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["industry_id"], ["industries.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("company_id", "industry_id"),
    )


def downgrade() -> None:
    op.drop_table("company_industries")
