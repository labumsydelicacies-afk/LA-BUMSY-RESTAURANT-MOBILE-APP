"""add rider first and last name fields

Revision ID: a3b3db4b8883
Revises: 3c7b37918781
Create Date: 2026-05-02 19:45:39.348132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b3db4b8883'
down_revision: Union[str, Sequence[str], None] = '3c7b37918781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
