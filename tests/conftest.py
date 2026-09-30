from common.jsonpath_utils import extract_one
import os
from contextlib import suppress
from uuid import uuid4

import pytest
import requests

from common.api_client import ApiClient
from common.config import resolve_base_url
from common.log_config import setup_logging


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=None,
        help="被测服务地址；优先于 TEST_BASE_URL 环境变量",
    )


def _register_test_user(client):
    suffix = uuid4().hex
    user_data = {
        "username": f"api_test_{suffix}",
        "email": f"api_test_{suffix}@example.com",
        "password": "TestPassword123!",
    }
    response = client.request("POST", "/auth/register", json=user_data)
    assert response.status_code == 201, f"测试用户注册失败：{response.text}"
    return user_data


def _login_test_user(client, user_data):
    response = client.request(
        "POST",
        "/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]},
    )
    assert response.status_code == 200, f"测试用户登录失败：{response.text}"
    token = extract_one(response.json(), "$.access_token")
    assert isinstance(token, str) and token, "登录响应缺少 access_token"
    client.session.headers["Authorization"] = f"Bearer {token}"


@pytest.fixture
def base_url(request):
    return resolve_base_url(
        cli_value=request.config.getoption("--base-url"),
        env_value=os.getenv("TEST_BASE_URL"),
    )


@pytest.fixture(scope="function")
def api_client(base_url):
    client = ApiClient(base_url)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="function")
def registered_user(api_client):
    user_data = _register_test_user(api_client)
    yield user_data

    # 被测服务没有删除用户的接口；清理当前客户端的认证状态。
    api_client.session.headers.pop("Authorization", None)


@pytest.fixture(scope="function")
def authenticated_client(api_client, registered_user):
    _login_test_user(api_client, registered_user)

    try:
        yield api_client
    finally:
        api_client.session.headers.pop("Authorization", None)


@pytest.fixture(scope="function")
def second_authenticated_client(base_url):
    client = ApiClient(base_url)
    try:
        user_data = _register_test_user(client)
        _login_test_user(client, user_data)
        yield client
    finally:
        # 只清理第二个账号的购物车；服务没有删除用户的接口。
        if "Authorization" in client.session.headers:
            with suppress(requests.RequestException):
                client.request("DELETE", "/cart")
        client.session.headers.pop("Authorization", None)
        client.close()



def pytest_configure(config):
    setup_logging()
