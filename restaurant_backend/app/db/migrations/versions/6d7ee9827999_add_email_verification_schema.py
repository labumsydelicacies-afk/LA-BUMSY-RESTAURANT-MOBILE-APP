"""add email verification schema

Revision ID: 6d7ee9827999
Revises: 2d78ff3f1728
Create Date: 2026-04-29 16:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6d7ee9827999"
down_revision: Union[str, Sequence[str], None] = "2d78ff3f1728"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_verified", server_default=None)

    op.create_table(
        "email_verification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_id"),
        "email_verification",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_user_id"),
        "email_verification",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_email_verification_user_id"), table_name="email_verification")
    op.drop_index(op.f("ix_email_verification_id"), table_name="email_verification")
    op.drop_table("email_verification")
    op.drop_column("users", "is_verified")
