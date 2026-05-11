from app.schemas.order import OrderCreate, OrderItemCreate
from app.schemas.food import FoodCreate
from app.schemas.user import UserCreate
from app.services.auth_service import authenticate_user, login_user
from app.services.food_service import create_food
from app.services.order_service import create_order
from app.services.user_service import create_user


def test_create_user_hashes_password(db_session):
    user = create_user(
        db_session,
        UserCreate(email="unit-user@test.com", password="Password123!", role="customer"),
    )
    assert user.hashed_password != "Password123!"
    assert user.is_email_verified is False


def test_authenticate_requires_verified_email(db_session):
    user = create_user(
        db_session,
        UserCreate(email="unverified@test.com", password="Password123!", role="customer"),
    )
    assert user.is_email_verified is False
    try:
        authenticate_user(db_session, "unverified@test.com", "Password123!")
        assert False, "Expected ValueError for unverified email"
    except ValueError as exc:
        assert "Email not verified" in str(exc)


def test_login_returns_jwt_for_verified_user(db_session):
    user = create_user(
        db_session,
        UserCreate(email="verified@test.com", password="Password123!", role="customer"),
    )
    user.is_email_verified = True
    db_session.commit()
    token = login_user(db_session, "verified@test.com", "Password123!")
    assert token is not None
    assert token["token_type"] == "bearer"
    assert isinstance(token["access_token"], str)


def test_order_rejects_negative_quantity(db_session, normal_user, sample_food):
    try:
        OrderCreate(items=[OrderItemCreate(food_id=sample_food.id, quantity=-1)])
        assert False, "Expected schema validation error for negative quantity"
    except Exception as exc:
        assert "greater than 0" in str(exc)


def test_create_food_rejects_duplicate_name(db_session):
    create_food(
        db_session,
        FoodCreate(name="Amala", price=2500.0, description=None, image_url=None, is_available=True),
    )
    try:
        create_food(
            db_session,
            FoodCreate(name="Amala", price=2500.0, description=None, image_url=None, is_available=True),
        )
        assert False, "Expected ValueError for duplicate food name"
    except ValueError as exc:
        assert "already exists" in str(exc)
