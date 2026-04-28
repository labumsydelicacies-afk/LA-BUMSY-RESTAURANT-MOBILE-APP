"""Ad-hoc smoke tests for the order service layer."""

from app.db.models import Order, User
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import (
    cancel_order,
    create_order,
    get_all_orders,
    get_order_by_id,
    get_orders_by_status,
    get_orders_by_user,
    update_order_status,
)
from app.tests.helpers import configure_output, db_session, print_footer, print_header
from app.utils.security import hash_password


def delete_orders_for_user(db, user_id: int) -> None:
    orders = db.query(Order).filter(Order.user_id == user_id).all()
    for order in orders:
        db.delete(order)
    db.flush()


def main() -> None:
    configure_output()
    print_header("ORDER SERVICE LAYER TEST")

    with db_session() as db:
        test_email = "ordertest@restaurant.com"
        test_password = "password123"
        test_nickname = "OrderTester"
        test_food_id = 1
        test_food_id2 = 2

        new_order = None
        cancellable_order = None
        test_user = None

        try:
            print("\n[SETUP] Creating test user directly in DB...")
            existing = db.query(User).filter(User.email == test_email).first()
            if existing:
                delete_orders_for_user(db, existing.id)
                db.delete(existing)
                db.commit()
                print(f"  Cleared leftover test user (ID: {existing.id})")

            test_user = User(
                email=test_email,
                hashed_password=hash_password(test_password),
                nickname=test_nickname,
                is_admin=False,
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            test_user_id = test_user.id
            print(f"  Test user created : {test_user.email} (ID: {test_user_id})")

            print("\n[TEST 1] Creating a valid order...")
            new_order = create_order(
                db,
                user_id=test_user_id,
                order_data=OrderCreate(
                    items=[
                        OrderItemCreate(food_id=test_food_id, quantity=2),
                        OrderItemCreate(food_id=test_food_id2, quantity=1),
                    ]
                ),
            )
            print(f"  Order created : ID {new_order.id}")
            print(f"  Total price   : ${new_order.total_price}")
            print(f"  Status        : {new_order.status}")

            print("\n[TEST 2] Creating empty order (should fail)...")
            try:
                create_order(db, user_id=test_user_id, order_data=OrderCreate(items=[]))
            except Exception as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 3] Creating order with invalid food ID (should fail)...")
            try:
                create_order(
                    db,
                    user_id=test_user_id,
                    order_data=OrderCreate(items=[OrderItemCreate(food_id=99999, quantity=1)]),
                )
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 4] Creating order with zero quantity (should fail)...")
            try:
                create_order(
                    db,
                    user_id=test_user_id,
                    order_data=OrderCreate(items=[OrderItemCreate(food_id=test_food_id, quantity=0)]),
                )
            except Exception as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 5] Fetching order by ID...")
            order = get_order_by_id(db, new_order.id)
            print(f"  Found : ID {order.id} | ${order.total_price} | {order.status}" if order else "  Order not found")

            print("\n[TEST 6] Fetching all orders for user...")
            user_orders = get_orders_by_user(db, test_user_id)
            print(f"  Total orders for user {test_user_id} : {len(user_orders)}")
            for order in user_orders:
                print(f"     - Order ID {order.id} | ${order.total_price} | {order.status}")

            print("\n[TEST 7] Fetching all orders as admin...")
            all_orders = get_all_orders(db)
            print(f"  Total orders in DB : {len(all_orders)}")

            print("\n[TEST 8] Fetching orders by status 'pending'...")
            pending_orders = get_orders_by_status(db, "pending")
            print(f"  Pending orders : {len(pending_orders)}")

            print("\n[TEST 9] Fetching with invalid status (should fail)...")
            try:
                get_orders_by_status(db, "flying")
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 10] Updating order status to confirmed...")
            updated = update_order_status(db, new_order.id, "confirmed")
            print(f"  Status updated : {updated.status}")

            print("\n[TEST 11] Updating order status to preparing...")
            updated = update_order_status(db, new_order.id, "preparing")
            print(f"  Status updated : {updated.status}")

            print("\n[TEST 12] Moving status backwards (should fail)...")
            try:
                update_order_status(db, new_order.id, "pending")
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 13] Updating to invalid status (should fail)...")
            try:
                update_order_status(db, new_order.id, "exploded")
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 14] Cancelling order that is preparing (should fail)...")
            try:
                cancel_order(db, new_order.id, test_user_id)
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 15] Creating a fresh order to cancel...")
            cancellable_order = create_order(
                db,
                user_id=test_user_id,
                order_data=OrderCreate(items=[OrderItemCreate(food_id=test_food_id, quantity=1)]),
            )
            print(f"  Fresh order created : ID {cancellable_order.id} | {cancellable_order.status}")

            print("\n[TEST 16] Cancelling fresh order...")
            cancelled = cancel_order(db, cancellable_order.id, test_user_id)
            print(f"  Order cancelled : {cancelled.status}")

            print("\n[TEST 17] Cancelling already cancelled order (should fail)...")
            try:
                cancel_order(db, cancellable_order.id, test_user_id)
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 18] Cancelling order with wrong user ID (should fail)...")
            try:
                cancel_order(db, new_order.id, user_id=99999)
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

        except Exception as exc:
            print(f"\n  Unexpected crash: {exc}")
            raise
        finally:
            print("\n[CLEANUP] Removing all test data...")
            try:
                if test_user is not None:
                    delete_orders_for_user(db, test_user.id)
                    db.commit()
                    print("  Test orders deleted")

                    db.delete(test_user)
                    db.commit()
                    print(f"  Test user deleted: {test_email}")
            except Exception as cleanup_error:
                db.rollback()
                print(f"  Cleanup failed: {cleanup_error}")

    print_footer()


if __name__ == "__main__":
    main()
