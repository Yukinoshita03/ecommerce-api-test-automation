import json as json_module

import allure
import pytest
import requests

from common.ai.client import AIClientError, OpenAICompatibleClient
from common.ai.analyzer import FailureAnalyzer


@allure.feature("模型调用客户端")
@allure.title("发送脱敏上下文并解析兼容接口响应")
def test_ai_client_request_and_response(monkeypatch):
    result = {"category": "assertion_mismatch", "summary": "名称不同", "hypotheses": [], "next_checks": ["核对数据"]}

    def fake_post(url, headers, json, timeout):
        assert url == "https://model.example/v1/chat/completions"
        assert headers == {"Authorization": "Bearer dummy-key"}
        assert json["model"] == "dummy-model"
        assert json["stream"] is False
        assert timeout == 30
        assert "private-password" not in json["messages"][1]["content"]
        response = requests.Response()
        response.status_code = 200
        response._content = json_module.dumps({"choices": [{"message": {"content": json_module.dumps(result)}}]}).encode()
        return response

    monkeypatch.setattr(requests, "post", fake_post)
    client = OpenAICompatibleClient("https://model.example/v1/chat/completions", "dummy-key", "dummy-model")
    assert FailureAnalyzer(client).analyze({"assertion_message": "名称不符", "password": "private-password"}) == result


@allure.feature("模型调用客户端")
@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"message": {"content": "not JSON"}}]}])
def test_ai_client_rejects_invalid_response(monkeypatch, body):
    response = requests.Response()
    response.status_code = 200
    response._content = json_module.dumps(body).encode()
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: response)
    with pytest.raises(AIClientError, match="有效的 JSON"):
        OpenAICompatibleClient("https://model.example/chat/completions", "dummy-key", "dummy-model").analyze({})


@allure.feature("模型调用客户端")
def test_ai_client_timeout_hides_error_details(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.Timeout("sensitive-provider-details")
    monkeypatch.setattr(requests, "post", fake_post)
    with pytest.raises(AIClientError) as error:
        OpenAICompatibleClient("https://model.example/chat/completions", "dummy-key", "dummy-model").analyze({})
    assert str(error.value) == "模型请求失败：Timeout"


@allure.feature("模型调用客户端")
def test_ai_client_http_error(monkeypatch):
    response = requests.Response()
    response.status_code = 401
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: response)
    with pytest.raises(AIClientError, match="HTTP 401"):
        OpenAICompatibleClient("https://model.example/chat/completions", "dummy-key", "dummy-model").analyze({})
