"""手动启用的 Hook 学习演示，不发请求、不修改数据库。"""

import os
import json
import logging

import requests
from common.api_client import ApiClient

import allure
import pytest


@pytest.mark.skipif(
    os.getenv("RUN_HOOK_DEMO") != "1",
    reason="故意失败的 Hook 演示，设置 RUN_HOOK_DEMO=1 才执行",
)
@allure.feature("pytest Hook 演示")
@allure.title("模拟业务断言失败，观察 call 阶段报告")
def test_hook_reports_assertion_failure(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="common.api_client")
    client = ApiClient("http://hook-demo.example")

    def fake_request(method, url, **kwargs):
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps({"id": 1, "name": "Mouse"}).encode()
        return response

    monkeypatch.setattr(client.session, "request", fake_request)
    try:
        response = client.request("GET", "/products/1")
        with allure.step("核对模拟商品名称，故意触发失败"):
            assert response.status_code == 200
            product = response.json()
            assert product["name"] == "Keyboard", "演示：商品名称不符合预期"
    finally:
        client.close()
