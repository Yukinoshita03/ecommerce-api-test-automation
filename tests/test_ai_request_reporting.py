"""请求层只负责返回响应、传播异常，不决定是否调用模型。"""
import json

import allure
import pytest
import requests

from common.api_client import ApiClient


@allure.feature("AI 分析触发边界")
@pytest.mark.parametrize("status", [200, 401, 404, 422, 500])
def test_request_does_not_call_model(monkeypatch, status):
    monkeypatch.setenv("AI_ANALYSIS_MODE", "real")
    def forbidden(*args, **kwargs):
        pytest.fail("请求层不应调用模型")
    monkeypatch.setattr(requests, "post", forbidden)
    client = ApiClient("http://example.test")
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps({"status": status}).encode()
    monkeypatch.setattr(client.session, "request", lambda *args, **kwargs: response)
    try:
        assert client.request("GET", "/products/1") is response
    finally:
        client.close()


@allure.feature("AI 分析触发边界")
def test_expected_timeout_does_not_call_model(monkeypatch):
    monkeypatch.setenv("AI_ANALYSIS_MODE", "real")
    def forbidden(*args, **kwargs):
        pytest.fail("预期异常不应在请求层触发模型")
    monkeypatch.setattr(requests, "post", forbidden)
    client = ApiClient("http://example.test")
    original = requests.Timeout("mock timeout")
    def fake_request(*args, **kwargs):
        raise original
    monkeypatch.setattr(client.session, "request", fake_request)
    try:
        with pytest.raises(requests.Timeout) as error:
            client.request("GET", "/products/1")
        assert error.value is original
    finally:
        client.close()
