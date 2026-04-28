"""Ad-hoc smoke tests for the user service layer."""

from app.schemas.user import UserCreate
from app.services.user_service import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
)
from app.tests.helpers import configure_output, db_session, print_footer, print_header


def main() -> None:
    configure_output()
    print_header("USER SERVICE LAYER TEST")

    with db_session() as db:
        new_user = None

        try:
            print("\n[TEST 1] Creating a new user...")
            new_user = create_user(
                db,
                UserCreate(
                    email="testuser@restaurant.com",
                    password="securepassword123",
                    nickname="TestUser",
                ),
            )
            print(f"  User created    : {new_user.email}")
            print(f"  Nickname        : {new_user.nickname}")
            print(f"  Is Admin        : {new_user.is_admin}")
            print(f"  Hashed Password : {new_user.hashed_password[:30]}...")

            print("\n[TEST 2] Creating duplicate user (should fail)...")
            try:
                create_user(
                    db,
                    UserCreate(
                        email="testuser@restaurant.com",
                        password="anotherpassword123",
                        nickname="AnotherUser",
                    ),
                )
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 3] Fetching user by email...")
            fetched = get_user_by_email(db, "testuser@restaurant.com")
            if fetched:
                print(f"  Found user : {fetched.email}")
            else:
                print("  User not found")

            print("\n[TEST 4] Fetching user by ID...")
            fetched_by_id = get_user_by_id(db, new_user.id)
            if fetched_by_id:
                print(f"  Found user : {fetched_by_id.email} (ID: {fetched_by_id.id})")
            else:
                print("  User not found")

            print("\n[TEST 5] Fetching all users...")
            all_users = get_all_users(db)
            print(f"  Total users in DB : {len(all_users)}")
            for user in all_users:
                print(f"     - {user.email} (ID: {user.id})")

            print("\n[TEST 6] Creating user with short password (should fail)...")
            try:
                create_user(
                    db,
                    UserCreate(
                        email="shortpass@restaurant.com",
                        password="123",
                        nickname="ShortPassUser",
                    ),
                )
            except ValueError as exc:
                print(f"  Caught expected error : {exc}")

            print("\n[TEST 7] Deleting user...")
            deleted = delete_user(db, new_user.id)
            print(f"  User deleted : {deleted}")
            new_user = None

            print("\n[TEST 8] Deleting non existent user (should return False)...")
            deleted_again = delete_user(db, 99999)
            print(f"  Result : {deleted_again}")

        except Exception as exc:
            print(f"\n  Unexpected error : {exc}")
            raise
        finally:
            if new_user is not None:
                try:
                    delete_user(db, new_user.id)
                except Exception:
                    db.rollback()

    print_footer()


if __name__ == "__main__":
    main()
