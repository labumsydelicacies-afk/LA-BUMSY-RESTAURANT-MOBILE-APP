"""Ad-hoc smoke tests for the authentication service layer."""

from app.schemas.user import UserCreate
from app.services.auth_service import authenticate_user, login_user
from app.services.user_service import create_user, delete_user, get_user_by_email
from app.tests.helpers import configure_output, db_session, print_footer, print_header


def main() -> None:
    configure_output()
    print_header("AUTHENTICATION SERVICE LAYER TEST")

    test_email = "authtest@restaurant.com"
    test_password = "password123"
    test_nickname = "AuthTester"

    with db_session() as db:
        try:
            print("\n[TEST 1] Creating test user...")
            try:
                user = create_user(
                    db,
                    UserCreate(
                        email=test_email,
                        password=test_password,
                        nickname=test_nickname,
                    ),
                )
                print(f"  User created  : {user.email}")
                print(f"  Nickname      : {user.nickname}")
                print(f"  Is Admin      : {user.is_admin}")
            except ValueError as exc:
                print(f"  {exc} - continuing with existing user")

            print("\n[TEST 2] Authenticating with correct credentials...")
            auth_result = authenticate_user(db=db, email=test_email, password=test_password)
            if auth_result:
                print(f"  Authenticated : {auth_result.email}")
            else:
                print("  Authentication failed")

            print("\n[TEST 3] Logging in and getting token...")
            token_response = login_user(db=db, email=test_email, password=test_password)
            if token_response:
                print(f"  Token type    : {token_response['token_type']}")
                print(f"  Role          : {token_response['role']}")
                print(f"  Nickname      : {token_response['nickname']}")
                print(f"  Access token  : {token_response['access_token'][:40]}...")
            else:
                print("  Login failed")

            print("\n[TEST 4] Authenticating with wrong password...")
            wrong_pass = authenticate_user(db=db, email=test_email, password="wrongpassword")
            print(f"  Correctly rejected wrong password : {wrong_pass is None}")

            print("\n[TEST 5] Authenticating with wrong email...")
            wrong_email = authenticate_user(db=db, email="fake@gmail.com", password=test_password)
            print(f"  Correctly rejected unknown email : {wrong_email is None}")

            print("\n[TEST 6] Authenticating with empty email...")
            empty_email = authenticate_user(db=db, email="", password=test_password)
            print(f"  Correctly rejected empty email : {empty_email is None}")

            print("\n[TEST 7] Authenticating with empty password...")
            empty_pass = authenticate_user(db=db, email=test_email, password="")
            print(f"  Correctly rejected empty password : {empty_pass is None}")

        except Exception as exc:
            print(f"\n  Unexpected error : {exc}")
            raise
        finally:
            user = get_user_by_email(db, test_email)
            if user is not None:
                try:
                    deleted = delete_user(db, user.id)
                    print(f"\n[CLEANUP] Test user deleted : {deleted}")
                except Exception:
                    db.rollback()

    print_footer()


if __name__ == "__main__":
    main()
