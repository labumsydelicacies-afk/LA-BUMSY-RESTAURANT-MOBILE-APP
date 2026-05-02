"""add payment fields to orders

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 11:00:00.000000

Adds six payment-tracking columns to the orders table to support
Flutterwave payment integration. All new columns are either nullable
or carry a server_default, so this migration is safe to apply
against a live database with existing rows.

New columns:
    payment_status          VARCHAR  DEFAULT 'pending'       NOT NULL
    payment_reference       VARCHAR  UNIQUE  NULLABLE
    external_transaction_id VARCHAR  NULLABLE
    payment_provider        VARCHAR  DEFAULT 'flutterwave'   NOT NULL
    paid_at                 DATETIME NULLABLE
    currency                VARCHAR  DEFAULT 'NGN'           NOT NULL
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- payment_status ---
    # Existing rows (orders placed before payment integration) get
    # 'pending' so they are still visible and processable by admins.
    op.add_column(
        "orders",
        sa.Column(
            "payment_status",
            sa.String(),
            nullable=False,
            server_default="pending",
        ),
    )
    # Remove server_default after backfill so new code drives the value.
    op.alter_column("orders", "payment_status", server_default=None)

    # --- payment_reference (Flutterwave tx_ref) ---
    op.add_column(
        "orders",
        sa.Column("payment_reference", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_orders_payment_reference",
        "orders",
        ["payment_reference"],
        unique=True,
    )

    # --- external_transaction_id (Flutterwave numeric transaction id) ---
    op.add_column(
        "orders",
        sa.Column("external_transaction_id", sa.String(), nullable=True),
    )

    # --- payment_provider ---
    op.add_column(
        "orders",
        sa.Column(
            "payment_provider",
            sa.String(),
            nullable=False,
            server_default="flutterwave",
        ),
    )
    op.alter_column("orders", "payment_provider", server_default=None)

    # --- paid_at ---
    op.add_column(
        "orders",
        sa.Column("paid_at", sa.DateTime(), nullable=True),
    )

    # --- currency ---
    op.add_column(
        "orders",
        sa.Column(
            "currency",
            sa.String(),
            nullable=False,
            server_default="NGN",
        ),
    )
    op.alter_column("orders", "currency", server_default=None)


def downgrade() -> None:
    op.drop_column("orders", "currency")
    op.drop_column("orders", "paid_at")
    op.drop_column("orders", "payment_provider")
    op.drop_column("orders", "external_transaction_id")
    op.drop_index("ix_orders_payment_reference", table_name="orders")
    op.drop_column("orders", "payment_reference")
    op.drop_column("orders", "payment_status")
