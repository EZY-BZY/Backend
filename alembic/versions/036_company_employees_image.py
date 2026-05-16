"""Add profile image URL to company_employees.

Revision ID: 036
Revises: 035
Create Date: 2026-05-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "036"
down_revision: Union[str, None] = "035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "company_employees",
        sa.Column("image", sa.String(2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("company_employees", "image")
