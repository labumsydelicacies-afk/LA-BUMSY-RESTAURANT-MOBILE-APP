"""add delivery system

Revision ID: a1b2c3d4e5f6
Revises: 6d7ee9827999
Create Date: 2026-05-01 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6d7ee9827999"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users: add is_rider column ---
    op.add_column(
        "users",
        sa.Column("is_rider", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "is_rider", server_default=None)

    # --- orders: add rider_id FK column ---
    op.add_column(
        "orders",
        sa.Column("rider_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_orders_rider_id", "orders", ["rider_id"], unique=False)
    op.create_foreign_key(
        "fk_orders_rider_id_users",
        "orders",
        "users",
        ["rider_id"],
        ["id"],
    )

    # --- deliveries table ---
    op.create_table(
        "deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("rider_id", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("picked_up_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["rider_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(op.f("ix_deliveries_id"), "deliveries", ["id"], unique=False)
    op.create_index(op.f("ix_deliveries_order_id"), "deliveries", ["order_id"], unique=True)
    op.create_index(op.f("ix_deliveries_rider_id"), "deliveries", ["rider_id"], unique=False)

    # --- delivery_verifications table ---
    op.create_table(
        "delivery_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("otp_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
    )
    op.create_index(
        op.f("ix_delivery_verifications_id"), "delivery_verifications", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_delivery_verifications_order_id"),
        "delivery_verifications",
        ["order_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_delivery_verifications_order_id"), table_name="delivery_verifications")
    op.drop_index(op.f("ix_delivery_verifications_id"), table_name="delivery_verifications")
    op.drop_table("delivery_verifications")

    op.drop_index(op.f("ix_deliveries_rider_id"), table_name="deliveries")
    op.drop_index(op.f("ix_deliveries_order_id"), table_name="deliveries")
    op.drop_index(op.f("ix_deliveries_id"), table_name="deliveries")
    op.drop_table("deliveries")

    op.drop_constraint("fk_orders_rider_id_users", "orders", type_="foreignkey")
    op.drop_index("ix_orders_rider_id", table_name="orders")
    op.drop_column("orders", "rider_id")

    op.drop_column("users", "is_rider")
