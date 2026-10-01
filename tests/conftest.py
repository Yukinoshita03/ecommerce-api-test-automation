import json
from datetime import datetime, timezone
from pathlib import Path
import warnings

import allure
from common.failure_context import start_context, finish_context, build_failure_context
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
    parser.addoption("--failure-dir", default="reports/failures", help="失败上下文 JSON 的输出目录")
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
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    config._failure_output_dir = Path(config.getoption("--failure-dir")) / run_id


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    # 覆盖本次测试的 setup、call 和 teardown，结束后释放收集状态。
    token = start_context()
    try:
        yield
    finally:
        finish_context(token)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # 暂停当前 Hook，让 pytest 和其他 Hook 生成本阶段执行报告。
    outcome = yield
    report = outcome.get_result()

    # setup、call、teardown 各生成一次报告，只输出失败的阶段。
    if report.failed:
        print(
            f"\n[失败报告 Hook]"
            f"\n失败用例：{report.nodeid}"
            f"\n失败阶段：{report.when}"
        )

        context = build_failure_context(report, call)
        try:
            output_dir = item.config._failure_output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{uuid4().hex}-{report.when}.json"
            content = json.dumps(context, ensure_ascii=False, indent=2, default=str)
            output_file.write_text(content, encoding="utf-8")
            allure.attach(content, name=f"失败上下文 ({report.when})", attachment_type=allure.attachment_type.JSON)
            print(f"失败上下文：{output_file.resolve()}")
        except OSError as error:
            warnings.warn(f"失败上下文写入失败：{type(error).__name__}", RuntimeWarning)
