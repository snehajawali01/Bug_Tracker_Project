
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from app.core.security import hash_password
from app.models import User, UserRole


def create_token(payload):
    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def test_missing_authentication_token(client):
    response = client.get("/api/bugs/")

    assert response.status_code == 401


def test_invalid_authentication_token(client):
    response = client.get(
        "/api/bugs/",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_expired_authentication_token(client):
    token = create_token({
        "sub": "1",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    })

    response = client.get(
        "/api/bugs/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_token_without_user_id(client):
    token = create_token({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    })

    response = client.get(
        "/api/bugs/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_token_for_nonexistent_user(client):
    token = create_token({
        "sub": "9999",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    })

    response = client.get(
        "/api/bugs/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


def test_inactive_user_cannot_access_api(client, db):
    inactive_user = User(
        full_name="Inactive User",
        username="inactiveuser",
        email="inactive@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=UserRole.TESTER,
        is_active=False,
    )

    db.add(inactive_user)
    db.commit()
    db.refresh(inactive_user)

    token = create_token({
        "sub": str(inactive_user.id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    })

    response = client.get(
        "/api/bugs/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
