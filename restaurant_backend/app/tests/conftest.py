from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Food, User
from app.main import app
from app.utils.security import UserRole, create_access_token, hash_password


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> TestClient:
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_startup = list(app.router.on_startup)
    app.router.on_startup = []
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    app.router.on_startup = original_startup


def _create_user(
    db: Session,
    *,
    email: str,
    password: str = "Password123!",
    is_admin: bool = False,
    is_verified: bool = True,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        nickname=email.split("@")[0],
        is_admin=is_admin,
        is_rider=False,
        is_email_verified=is_verified,
        is_profile_complete=True,
        phone="08000000000",
        address="123 Test Street",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    return _create_user(db_session, email="admin@test.com", is_admin=True)


@pytest.fixture
def normal_user(db_session: Session) -> User:
    return _create_user(db_session, email="user@test.com", is_admin=False)


@pytest.fixture
def unverified_user(db_session: Session) -> User:
    return _create_user(db_session, email="pending@test.com", is_verified=False)


@pytest.fixture
def sample_food(db_session: Session) -> Food:
    food = Food(name="Jollof Rice", price=3500.0, description="Smoky rice")
    db_session.add(food)
    db_session.commit()
    db_session.refresh(food)
    return food


def auth_header_for(user: User, role: UserRole | None = None, *, expired: bool = False) -> dict[str, str]:
    chosen_role = role or (UserRole.ADMIN if user.is_admin else UserRole.CUSTOMER)
    if expired:
        payload = {
            "sub": user.email,
            "user_id": user.id,
            "role": chosen_role.value,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
        }
        from jose import jwt
        from app.config import ALGORITHM, SECRET_KEY

        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    else:
        token = create_access_token(
            {
                "sub": user.email,
                "user_id": user.id,
                "nickname": user.nickname,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "address": user.address,
                "user_state": "ACTIVE",
            },
            role=chosen_role,
        )
    return {"Authorization": f"Bearer {token}"}
