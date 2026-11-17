
from app.models import User, UserRole
from app.core.security import hash_password


def create_test_user(db, username, email, role):
    user = User(
        full_name=f"Test {username}",
        username=username,
        email=email,
        password_hash=hash_password("TestPassword123!"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_headers(client, username):
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": username,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def test_bug_crud_operations(client):
    registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Bug Tester",
            "email": "bugtester@example.com",
            "username": "bugtester",
            "password": "TestPassword123!",
        },
    )
    assert registration.status_code == 201

    headers = get_auth_headers(client, "bugtester")

    create_response = client.post(
        "/api/bugs/",
        headers=headers,
        json={
            "title": "Login page error",
            "description": "Login page displays an error.",
            "priority": "high",
        },
    )

    assert create_response.status_code == 201
    bug_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/bugs/{bug_id}",
        headers=headers,
    )
    assert get_response.status_code == 200

    update_response = client.put(
        f"/api/bugs/{bug_id}",
        headers=headers,
        json={
            "title": "Updated login page error",
            "priority": "critical",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["priority"] == "critical"

    delete_response = client.delete(
        f"/api/bugs/{bug_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200


def test_bug_filtering(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Filter Tester",
            "email": "filtertester@example.com",
            "username": "filtertester",
            "password": "TestPassword123!",
        },
    )

    headers = get_auth_headers(client, "filtertester")

    client.post(
        "/api/bugs/",
        headers=headers,
        json={
            "title": "Dashboard loading problem",
            "description": "Dashboard loads very slowly.",
            "priority": "high",
        },
    )

    response = client.get(
        "/api/bugs/",
        headers=headers,
        params={
            "priority": "high",
            "bug_status": "open",
            "search": "Dashboard",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Dashboard loading problem"


def test_admin_can_assign_bug(client, db):
    reporter = create_test_user(
        db,
        "reporter01",
        "reporter@example.com",
        UserRole.TESTER,
    )

    developer = create_test_user(
        db,
        "developer02",
        "developer02@example.com",
        UserRole.DEVELOPER,
    )

    create_test_user(
        db,
        "admin02",
        "admin02@example.com",
        UserRole.ADMIN,
    )

    reporter_headers = get_auth_headers(client, "reporter01")
    admin_headers = get_auth_headers(client, "admin02")
    developer_headers = get_auth_headers(client, "developer02")

    bug_response = client.post(
        "/api/bugs/",
        headers=reporter_headers,
        json={
            "title": "Payment page issue",
            "description": "Payment page is not loading.",
            "priority": "medium",
        },
    )

    assert bug_response.status_code == 201
    bug_id = bug_response.json()["id"]

    assignment_response = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=admin_headers,
        json={"assignee_id": developer.id},
    )

    assert assignment_response.status_code == 200
    assert assignment_response.json()["assignee_id"] == developer.id

    developer_bugs = client.get(
        "/api/bugs/",
        headers=developer_headers,
    )

    assert developer_bugs.status_code == 200
    assert any(bug["id"] == bug_id for bug in developer_bugs.json())


def test_non_admin_cannot_assign_bug(client, db):
    tester = create_test_user(
        db,
        "tester02",
        "tester02@example.com",
        UserRole.TESTER,
    )

    developer = create_test_user(
        db,
        "developer03",
        "developer03@example.com",
        UserRole.DEVELOPER,
    )

    tester_headers = get_auth_headers(client, "tester02")

    bug_response = client.post(
        "/api/bugs/",
        headers=tester_headers,
        json={
            "title": "Search page issue",
            "description": "Search results are not displayed.",
            "priority": "low",
        },
    )

    assert bug_response.status_code == 201
    bug_id = bug_response.json()["id"]

    assignment_response = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=tester_headers,
        json={"assignee_id": developer.id},
    )

    assert assignment_response.status_code == 403
