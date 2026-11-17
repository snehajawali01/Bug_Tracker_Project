
def test_user_registration(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "newuser@example.com",
            "username": "newuser01",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == "newuser01"
    assert response.json()["email"] == "newuser@example.com"


def test_user_login(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "loginuser@example.com",
            "username": "loginuser01",
            "password": "TestPassword123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "loginuser01",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_with_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Test User",
            "email": "wrongpass@example.com",
            "username": "wrongpass01",
            "password": "TestPassword123!",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "wrongpass01",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_duplicate_email_registration(client):
    user_data = {
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "username": "duplicate01",
        "password": "TestPassword123!",
    }

    first_response = client.post(
        "/api/auth/register",
        json=user_data,
    )

    second_response = client.post(
        "/api/auth/register",
        json={
            **user_data,
            "username": "duplicate02",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
