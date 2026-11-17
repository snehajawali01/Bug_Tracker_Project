
def register_and_login(client, username, email):
    registration = client.post(
        "/api/auth/register",
        json={
            "full_name": "Comment Tester",
            "email": email,
            "username": username,
            "password": "TestPassword123!",
        },
    )

    assert registration.status_code == 201

    login = client.post(
        "/api/auth/login",
        json={
            "username_or_email": username,
            "password": "TestPassword123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_test_bug(client, headers):
    response = client.post(
        "/api/bugs/",
        headers=headers,
        json={
            "title": "Comment testing bug",
            "description": "This bug is created to test comments.",
            "priority": "medium",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_comment_crud_operations(client):
    headers = register_and_login(
        client,
        "commentuser",
        "commentuser@example.com",
    )

    bug_id = create_test_bug(client, headers)

    create_response = client.post(
        f"/api/bugs/{bug_id}/comments",
        headers=headers,
        json={
            "content": "This is my first automated test comment."
        },
    )

    assert create_response.status_code == 201

    comment_id = create_response.json()["id"]

    get_response = client.get(
        f"/api/bugs/{bug_id}/comments",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert len(get_response.json()) == 1

    update_response = client.put(
        f"/api/comments/{comment_id}",
        headers=headers,
        json={
            "content": "This comment has been updated."
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["content"] == (
        "This comment has been updated."
    )

    delete_response = client.delete(
        f"/api/comments/{comment_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    final_response = client.get(
        f"/api/bugs/{bug_id}/comments",
        headers=headers,
    )

    assert final_response.status_code == 200
    assert final_response.json() == []


def test_empty_comment_is_rejected(client):
    headers = register_and_login(
        client,
        "emptycomment",
        "emptycomment@example.com",
    )

    bug_id = create_test_bug(client, headers)

    response = client.post(
        f"/api/bugs/{bug_id}/comments",
        headers=headers,
        json={
            "content": "   "
        },
    )

    assert response.status_code == 422
