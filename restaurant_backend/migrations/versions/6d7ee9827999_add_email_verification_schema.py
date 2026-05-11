"""add email verification schema

Revision ID: 6d7ee9827999
Revises: 2d78ff3f1728
Create Date: 2026-04-29 16:20:00.000000

"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "6d7ee9827999"
down_revision: Union[str, Sequence[str], None] = "2d78ff3f1728"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This revision is intentionally a no-op.
    # The base schema revision already contains `users.is_verified`
    # and the `email_verification` table.
    pass


def downgrade() -> None:
    # No-op downgrade to mirror no-op upgrade.
    pass
