"""手动启用的失败报告演示；不访问网络或修改数据库。"""

import json
import logging
import os

import allure
import pytest
import requests

from common.api_client import ApiClient



def fake_request(method, url, **kwargs):
    response = requests.Response()
    response.status_code = 200
    response.encoding = "utf-8"
    response.headers["Content-Type"] = "application/json"
    response._content = json.dumps(
        {
            "id": 1,
            "name": "Mouse",
            "price": 25.0,
            "stock": 20,
            "access_token": "demo-token-must-not-leak",
        }
    ).encode("utf-8")
    return response


@pytest.mark.skipif(
    os.getenv("RUN_REPORT_FAILURE_DEMO") != "1",
    reason="故意失败的报告演示，设置 RUN_REPORT_FAILURE_DEMO=1 才执行",
)
@allure.feature("失败报告演示")
@allure.title("模拟商品名称不符合预期，验证失败证据")
def test_product_name_mismatch_report(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="common.api_client")
    client = ApiClient("http://report-demo.example")

    # 替换本客户端的发送方法：仍经过真实的日志及附件记录代码。
    monkeypatch.setattr(client.session, "request", fake_request)
    try:
        with allure.step("模拟查询商品：HTTP 200，但商品名称为 Mouse"):
            response = client.request("GET", "/products/1")

        with allure.step("检查 HTTP 状态码为 200"):
            assert response.status_code == 200

        with allure.step("核对商品名称：预期 Keyboard，实际 Mouse"):
            product = response.json()
            allure.attach(
                json.dumps(
                    {"expected_name": "Keyboard", "actual_name": product["name"]},
                    ensure_ascii=False,
                    indent=2,
                ),
                name="名称对比",
                attachment_type=allure.attachment_type.JSON,
            )
            # 故意失败，观察 Allure 的断言、步骤、附件及捕获日志。
            assert product["name"] == "Keyboard", "商品名称不符合预期"
    finally:
        client.close()
