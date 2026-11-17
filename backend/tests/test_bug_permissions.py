
from app.models import User, UserRole
from app.core.security import hash_password


def create_user(db, username, role):
    user = User(
        full_name=f"Test {username}",
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("TestPassword123!"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(client, username):
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": username,
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def create_bug(client, headers):
    response = client.post(
        "/api/bugs/",
        headers=headers,
        json={
            "title": "Permission test bug",
            "description": "Testing bug permissions.",
            "priority": "high",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_user_cannot_access_another_users_bug(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "First Tester",
            "email": "first@example.com",
            "username": "firsttester",
            "password": "TestPassword123!",
        },
    )

    client.post(
        "/api/auth/register",
        json={
            "full_name": "Second Tester",
            "email": "second@example.com",
            "username": "secondtester",
            "password": "TestPassword123!",
        },
    )

    first_headers = login(client, "firsttester")
    second_headers = login(client, "secondtester")

    bug_id = create_bug(client, first_headers)

    response = client.get(
        f"/api/bugs/{bug_id}",
        headers=second_headers,
    )

    assert response.status_code == 404


def test_assignee_cannot_update_or_delete_bug(client, db):
    reporter = create_user(db, "permissionreporter", UserRole.TESTER)
    developer = create_user(db, "permissiondeveloper", UserRole.DEVELOPER)
    admin = create_user(db, "permissionadmin", UserRole.ADMIN)

    reporter_headers = login(client, reporter.username)
    developer_headers = login(client, developer.username)
    admin_headers = login(client, admin.username)

    bug_id = create_bug(client, reporter_headers)

    assignment = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=admin_headers,
        json={"assignee_id": developer.id},
    )
    assert assignment.status_code == 200

    update_response = client.put(
        f"/api/bugs/{bug_id}",
        headers=developer_headers,
        json={"title": "Unauthorized update"},
    )
    assert update_response.status_code == 403

    delete_response = client.delete(
        f"/api/bugs/{bug_id}",
        headers=developer_headers,
    )
    assert delete_response.status_code == 403


def test_admin_cannot_assign_nonexistent_bug(client, db):
    admin = create_user(db, "missingbugadmin", UserRole.ADMIN)
    admin_headers = login(client, admin.username)

    response = client.post(
        "/api/bugs/99999/assign",
        headers=admin_headers,
        json={"assignee_id": None},
    )

    assert response.status_code == 404


def test_admin_cannot_assign_bug_to_invalid_assignee(client, db):
    admin = create_user(db, "invalidassignadmin", UserRole.ADMIN)
    admin_headers = login(client, admin.username)

    bug_id = create_bug(client, admin_headers)

    response = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=admin_headers,
        json={"assignee_id": admin.id},
    )

    assert response.status_code == 400


def test_admin_can_unassign_bug(client, db):
    reporter = create_user(db, "unassignreporter", UserRole.TESTER)
    developer = create_user(db, "unassigndeveloper", UserRole.DEVELOPER)
    admin = create_user(db, "unassignadmin", UserRole.ADMIN)

    reporter_headers = login(client, reporter.username)
    admin_headers = login(client, admin.username)

    bug_id = create_bug(client, reporter_headers)

    assignment = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=admin_headers,
        json={"assignee_id": developer.id},
    )
    assert assignment.status_code == 200

    response = client.post(
        f"/api/bugs/{bug_id}/assign",
        headers=admin_headers,
        json={"assignee_id": None},
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] is None
