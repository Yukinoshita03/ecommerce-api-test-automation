import json

import allure

from common.allure_reporting import attach_response, redact


@allure.feature("报告附件")
@allure.title("嵌套凭据脱敏且不改变原始数据")
def test_redact_nested_credentials():
    original = {"password": "test-secret", "items": [{"access_token": "test-token", "id": 1}], "Authorization": "Bearer test-token"}
    with allure.step("检查嵌套字典和列表中的凭据被隐藏"):
        assert redact(original) == {"password": "***", "items": [{"access_token": "***", "id": 1}], "Authorization": "***"}
        assert original["password"] == "test-secret"
        assert original["items"][0]["access_token"] == "test-token"


@allure.feature("报告附件")
@allure.title("响应附件保留状态码并隐藏 token")
def test_response_attachment_redacts_token(monkeypatch):
    captured = {}

    def fake_attach(body, name, attachment_type):
        captured["body"] = json.loads(body)

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"access_token": "test-token", "token_type": "bearer"}

    with allure.step("捕获附件内容并检查脱敏结果"):
        monkeypatch.setattr(allure, "attach", fake_attach)
        attach_response(FakeResponse())
        assert captured["body"] == {"status_code": 200, "body": {"access_token": "***", "token_type": "bearer"}}
