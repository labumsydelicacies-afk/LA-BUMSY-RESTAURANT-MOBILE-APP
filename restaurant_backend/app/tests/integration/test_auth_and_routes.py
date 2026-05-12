from app.db.models import User
from app.services.email_verification_service import create_otp
from app.utils.security import UserRole, create_access_token
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import ALGORITHM, SECRET_KEY


def auth_header_for(user: User, role: UserRole | None = None) -> dict[str, str]:
    chosen_role = role or (UserRole.ADMIN if user.is_admin else UserRole.CUSTOMER)
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


def test_auth_register_verify_login_flow(client, db_session):
    reg = client.post(
        "/auth/register",
        json={"email": "flow@test.com", "password": "Password123!", "role": "customer"},
    )
    assert reg.status_code == 201
    user_id = reg.json()["user"]["id"]

    otp = create_otp(db_session, user_id)

    verify = client.post("/auth/verify-otp", json={"user_id": user_id, "otp": otp})
    assert verify.status_code == 200

    login = client.post("/auth/login", json={"email": "flow@test.com", "password": "Password123!"})
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_protected_routes_require_token(client):
    response = client.get("/orders")
    assert response.status_code == 401


def test_admin_route_blocked_for_non_admin(client, normal_user):
    headers = auth_header_for(normal_user)
    response = client.get("/admin/users", headers=headers)
    assert response.status_code == 403


def test_food_crud_and_order_flow(client, admin_user, normal_user):
    admin_headers = auth_header_for(admin_user)
    user_headers = auth_header_for(normal_user)

    create_food = client.post(
        "/foods",
        headers=admin_headers,
        json={"name": "Egusi", "description": "Soup", "price": 4200, "image_url": None, "is_available": True},
    )
    assert create_food.status_code == 201
    food_id = create_food.json()["id"]

    list_foods = client.get("/foods")
    assert list_foods.status_code == 200
    assert any(item["id"] == food_id for item in list_foods.json())
    assert next(item for item in list_foods.json() if item["id"] == food_id)["is_available"] is True

    order = client.post("/orders", headers=user_headers, json={"items": [{"food_id": food_id, "quantity": 2}]})
    assert order.status_code == 201

    orders = client.get("/orders", headers=user_headers)
    assert orders.status_code == 200
    assert len(orders.json()) >= 1


def test_docs_loads_and_expected_routes_present(client):
    docs = client.get("/openapi.json")
    assert docs.status_code == 200
    paths = docs.json()["paths"].keys()
    assert any(p.startswith("/auth") for p in paths)
    assert any(p.startswith("/foods") for p in paths)
    assert any(p.startswith("/orders") for p in paths)
    assert any(p.startswith("/payments") for p in paths)
    assert any(p.startswith("/admin") for p in paths)


def test_invalid_login_and_duplicate_registration(client):
    first = client.post(
        "/auth/register",
        json={"email": "dupe@test.com", "password": "Password123!", "role": "customer"},
    )
    assert first.status_code == 201

    dupe = client.post(
        "/auth/register",
        json={"email": "dupe@test.com", "password": "Password123!", "role": "customer"},
    )
    assert dupe.status_code == 400

    invalid_login = client.post("/auth/login", json={"email": "dupe@test.com", "password": "wrong-pass"})
    assert invalid_login.status_code in (401, 422)


def test_expired_and_tampered_jwt_rejected(client, normal_user):
    expired_payload = {
        "sub": normal_user.email,
        "user_id": normal_user.id,
        "role": UserRole.CUSTOMER.value,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(expired_payload, SECRET_KEY, algorithm=ALGORITHM)
    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    expired = client.get("/orders", headers=expired_headers)
    assert expired.status_code == 401

    valid_headers = auth_header_for(normal_user)
    token = valid_headers["Authorization"].split(" ", 1)[1]
    tampered = token[:-2] + "xx"
    tampered_resp = client.get("/orders", headers={"Authorization": f"Bearer {tampered}"})
    assert tampered_resp.status_code == 401


def test_injection_and_input_manipulation_rejected(client, normal_user, admin_user):
    admin_headers = auth_header_for(admin_user)
    user_headers = auth_header_for(normal_user)
    food_resp = client.post(
        "/foods",
        headers=admin_headers,
        json={"name": "Fried Rice", "description": "Rice", "price": 3000, "image_url": None, "is_available": True},
    )
    food_id = food_resp.json()["id"]

    sql_like_login = client.post(
        "/auth/login",
        json={"email": "' OR 1=1 --", "password": "whatever"},
    )
    assert sql_like_login.status_code in (401, 422)

    negative_qty = client.post(
        "/orders",
        headers=user_headers,
        json={"items": [{"food_id": food_id, "quantity": -10}]},
    )
    assert negative_qty.status_code == 422

    malformed_json = client.post(
        "/orders",
        headers={**user_headers, "Content-Type": "application/json"},
        content='{"items": [}',
    )
    assert malformed_json.status_code == 422

    huge_payload = client.post(
        "/foods",
        headers=admin_headers,
        json={"name": "X" * 5000, "description": "Y" * 10000, "price": 1000, "image_url": None, "is_available": True},
    )
    assert huge_payload.status_code in (201, 400, 422)


def test_rate_abuse_smoke_no_crash(client):
    for i in range(20):
        response = client.post(
            "/auth/login",
            json={"email": f"nobody{i}@test.com", "password": "bad-pass"},
        )
        assert response.status_code in (401, 422)


def test_idor_protection_on_payment_order_ownership(client, normal_user, admin_user, db_session):
    other = User(
        email="other@test.com",
        hashed_password=normal_user.hashed_password,
        nickname="other",
        is_admin=False,
        is_rider=False,
        is_email_verified=True,
        is_profile_complete=True,
    )
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    admin_headers = auth_header_for(admin_user)
    user_headers = auth_header_for(normal_user)
    other_headers = auth_header_for(other)

    food_resp = client.post(
        "/foods",
        headers=admin_headers,
        json={"name": "Beans", "description": "Stew", "price": 1500, "image_url": None, "is_available": True},
    )
    food_id = food_resp.json()["id"]

    order_resp = client.post("/orders", headers=user_headers, json={"items": [{"food_id": food_id, "quantity": 1}]})
    order_id = order_resp.json()["id"]

    pay_attempt = client.post("/payments/initialize", headers=other_headers, json={"order_id": order_id})
    assert pay_attempt.status_code == 403


def test_admin_cannot_force_out_for_delivery_without_rider_acceptance(client, admin_user, normal_user):
    admin_headers = auth_header_for(admin_user)
    user_headers = auth_header_for(normal_user)

    food_resp = client.post(
        "/foods",
        headers=admin_headers,
        json={"name": "Jollof", "description": "Rice", "price": 2500, "image_url": None, "is_available": True},
    )
    food_id = food_resp.json()["id"]

    order_resp = client.post(
        "/orders",
        headers=user_headers,
        json={"items": [{"food_id": food_id, "quantity": 1}]},
    )
    order_id = order_resp.json()["id"]

    for next_status in ["pending", "confirmed", "preparing", "ready_for_pickup"]:
        update_resp = client.patch(
            f"/orders/{order_id}/status",
            headers=admin_headers,
            json={"status": next_status},
        )
        assert update_resp.status_code == 200

    blocked = client.patch(
        f"/orders/{order_id}/status",
        headers=admin_headers,
        json={"status": "out_for_delivery"},
    )
    assert blocked.status_code == 400
    assert "rider accepts" in blocked.json()["detail"].lower()
