from common.jsonpath_utils import extract_one
import json

import allure
import pytest

from common.allure_reporting import attach_response


@allure.feature("用户认证")
@allure.title("未登录时查询当前用户被拒绝")
def test_auth_me_requires_token(api_client):
    with allure.step("不携带 token，发送 GET /auth/me"):
        response = api_client.request("GET", "/auth/me")
        attach_response(response)

    with allure.step("检查 HTTP 状态码为 401"):
        assert response.status_code == 401, "未登录访问 /auth/me 应返回 401"


@pytest.mark.stateful
@allure.feature("用户认证")
@allure.title("登录后携带 token 查询当前用户")
def test_login_token_authenticates_registered_user(api_client, registered_user):
    # registered_user fixture 已经在测试开始前注册好账号。
    with allure.step("使用测试账号发送 POST /auth/login"):
        login_response = api_client.request(
            "POST",
            "/auth/login",
            data={
                "username": registered_user["username"],
                "password": registered_user["password"],
            },
        )
        # 登录响应包含 token，只记录状态码，避免把凭据写进报告。
        allure.attach(
            str(login_response.status_code),
            name="登录响应状态码",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("检查登录成功，返回非空的 Bearer token"):
        assert login_response.status_code == 200, "登录失败"
        login_body = login_response.json()
        assert login_body["token_type"].lower() == "bearer"
        access_token = extract_one(login_body, "$.access_token")
        assert access_token, "登录响应中的 access_token 为空"

    with allure.step("设置 Authorization 请求头，携带 token 发送 GET /auth/me"):
        api_client.session.headers["Authorization"] = f"Bearer {access_token}"
        response = api_client.request("GET", "/auth/me")
        attach_response(response)

    with allure.step("检查查询成功，用户名与刚注册的用户一致"):
        assert response.status_code == 200, "携带有效 token 访问 /auth/me 应返回 200"
        current_user = response.json()
        allure.attach(
            json.dumps({"expected_username": registered_user["username"], "actual_username": current_user["username"]}, ensure_ascii=False, indent=2),
            name="用户名核对",
            attachment_type=allure.attachment_type.JSON,
        )
        assert current_user["username"] == registered_user["username"], "当前用户与注册用户不一致"
