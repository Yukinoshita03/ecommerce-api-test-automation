import pytest


def test_auth_me_requires_token(api_client):
    response = api_client.request("GET", "/auth/me")

    assert response.status_code == 401, "未登录访问 /auth/me 应返回 401"


@pytest.mark.stateful
def test_login_token_authenticates_registered_user(api_client, registered_user):
    login_response = api_client.request(
        "POST",
        "/auth/login",
        data={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )

    assert login_response.status_code == 200, "登录失败"
    login_body = login_response.json()
    assert login_body["token_type"].lower() == "bearer"
    access_token = login_body["access_token"]
    assert access_token, "登录响应中的 access_token 为空"

    api_client.session.headers["Authorization"] = f"Bearer {access_token}"
    response = api_client.request("GET", "/auth/me")

    assert response.status_code == 200, "携带有效 token 访问 /auth/me 应返回 200"
    current_user = response.json()
    assert current_user["username"] == registered_user["username"]
