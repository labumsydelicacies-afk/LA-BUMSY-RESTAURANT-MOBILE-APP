"""merge delivery otp migration branch

Revision ID: e5f6a7b8c9d0
Revises: a3b3db4b8883, c4d5e6f7a8b9
Create Date: 2026-05-12 00:00:00.000000

This merge keeps the schema history linear after the delivery OTP column was
added on a separate Alembic branch. It intentionally performs no schema work.
"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = ("a3b3db4b8883", "c4d5e6f7a8b9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
