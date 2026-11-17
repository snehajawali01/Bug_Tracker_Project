
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
            "title": "Comment permission bug",
            "description": "Testing comment permissions.",
            "priority": "medium",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_comment(client, bug_id, headers):
    response = client.post(
        f"/api/bugs/{bug_id}/comments",
        headers=headers,
        json={"content": "Original test comment"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_comment_endpoints_reject_nonexistent_bug(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Comment Tester",
            "email": "commenttester@example.com",
            "username": "commenttester",
            "password": "TestPassword123!",
        },
    )
    headers = login(client, "commenttester")

    get_response = client.get(
        "/api/bugs/99999/comments",
        headers=headers,
    )
    assert get_response.status_code == 404

    post_response = client.post(
        "/api/bugs/99999/comments",
        headers=headers,
        json={"content": "Testing missing bug"},
    )
    assert post_response.status_code == 404


def test_nonexistent_comment_returns_404(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Missing Comment Tester",
            "email": "missingcomment@example.com",
            "username": "missingcomment",
            "password": "TestPassword123!",
        },
    )
    headers = login(client, "missingcomment")

    update_response = client.put(
        "/api/comments/99999",
        headers=headers,
        json={"content": "Updated comment"},
    )
    assert update_response.status_code == 404

    delete_response = client.delete(
        "/api/comments/99999",
        headers=headers,
    )
    assert delete_response.status_code == 404


def test_user_cannot_edit_another_users_comment(client, db):
    reporter = create_user(db, "commentreporter", UserRole.TESTER)
    developer = create_user(db, "commentdeveloper", UserRole.DEVELOPER)
    admin = create_user(db, "commentadmin", UserRole.ADMIN)

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

    comment_id = create_comment(client, bug_id, reporter_headers)

    response = client.put(
        f"/api/comments/{comment_id}",
        headers=developer_headers,
        json={"content": "Unauthorized edit"},
    )
    assert response.status_code == 403


def test_user_cannot_delete_another_users_comment(client, db):
    reporter = create_user(db, "deletereporter", UserRole.TESTER)
    developer = create_user(db, "deletedeveloper", UserRole.DEVELOPER)
    admin = create_user(db, "deleteadmin", UserRole.ADMIN)

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

    comment_id = create_comment(client, bug_id, reporter_headers)

    response = client.delete(
        f"/api/comments/{comment_id}",
        headers=developer_headers,
    )
    assert response.status_code == 403


def test_comment_cannot_be_updated_with_whitespace(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Whitespace Tester",
            "email": "whitespace@example.com",
            "username": "whitespacetester",
            "password": "TestPassword123!",
        },
    )
    headers = login(client, "whitespacetester")

    bug_id = create_bug(client, headers)
    comment_id = create_comment(client, bug_id, headers)

    response = client.put(
        f"/api/comments/{comment_id}",
        headers=headers,
        json={"content": "   "},
    )

    assert response.status_code == 422
