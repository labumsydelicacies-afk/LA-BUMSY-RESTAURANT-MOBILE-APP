"""Ad-hoc smoke tests for security helpers."""

from app.tests.helpers import configure_output, print_footer, print_header
from app.utils.security import (
    UserRole,
    create_access_token,
    get_user_email_from_token,
    hash_password,
    is_admin,
    verify_password,
)


def main() -> None:
    configure_output()
    print_header("SECURITY MODULE TEST")

    password = "mysecretpassword"
    hashed = hash_password(password)
    verified = verify_password(password, hashed)
    wrong = verify_password("wrongpassword", hashed)

    print("\n[PASSWORD HASHING]")
    print(f"  Original  : {password}")
    print(f"  Hashed    : {hashed}")
    print(f"  Correct   : {verified}")
    print(f"  Wrong     : {wrong}")

    customer_token = create_access_token(
        data={"sub": "customer@email.com"},
        role=UserRole.CUSTOMER,
    )
    print("\n[CUSTOMER TOKEN]")
    print(f"  Token     : {customer_token[:40]}...")
    print(f"  User      : {get_user_email_from_token(customer_token)}")
    print(f"  Is Admin  : {is_admin(customer_token)}")

    admin_token = create_access_token(
        data={"sub": "admin@restaurant.com"},
        role=UserRole.ADMIN,
    )
    print("\n[ADMIN TOKEN]")
    print(f"  Token     : {admin_token[:40]}...")
    print(f"  User      : {get_user_email_from_token(admin_token)}")
    print(f"  Is Admin  : {is_admin(admin_token)}")

    print_footer()


if __name__ == "__main__":
    main()
