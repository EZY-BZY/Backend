"""Add forgot-password OTP fields to owners and employees.

Revision ID: 015
Revises: 014
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_cols(table: str) -> None:
    op.add_column(table, sa.Column("forgot_password_otp_hash", sa.Text(), nullable=True))
    op.add_column(
        table, sa.Column("forgot_password_otp_expires_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        table, sa.Column("forgot_password_otp_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        table,
        sa.Column(
            "forgot_password_verify_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        table,
        sa.Column(
            "forgot_password_resend_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        table, sa.Column("forgot_password_last_sent_at", sa.DateTime(timezone=True), nullable=True)
    )

    op.create_index(f"ix_{table}_fp_expires_at", table, ["forgot_password_otp_expires_at"], unique=False)
    op.create_index(f"ix_{table}_fp_verified_at", table, ["forgot_password_otp_verified_at"], unique=False)

    op.alter_column(table, "forgot_password_verify_attempts", server_default=None)
    op.alter_column(table, "forgot_password_resend_attempts", server_default=None)


def _drop_cols(table: str) -> None:
    op.drop_index(f"ix_{table}_fp_verified_at", table_name=table)
    op.drop_index(f"ix_{table}_fp_expires_at", table_name=table)
    op.drop_column(table, "forgot_password_last_sent_at")
    op.drop_column(table, "forgot_password_resend_attempts")
    op.drop_column(table, "forgot_password_verify_attempts")
    op.drop_column(table, "forgot_password_otp_verified_at")
    op.drop_column(table, "forgot_password_otp_expires_at")
    op.drop_column(table, "forgot_password_otp_hash")


def upgrade() -> None:
    _add_cols("companies_owners")
    _add_cols("beasy_employees")


def downgrade() -> None:
    _drop_cols("beasy_employees")
    _drop_cols("companies_owners")

