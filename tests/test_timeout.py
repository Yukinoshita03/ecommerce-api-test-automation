import logging

import allure
import pytest
import requests

from common.api_client import ApiClient


@allure.feature('请求超时')
@allure.title('默认超时配置与 Timeout 传播')
def test_api_client_timeout(monkeypatch, caplog):
    with allure.step("执行场景并检查预期结果"):
        caplog.set_level(logging.INFO, logger="common.api_client")
        client = ApiClient("http://ading.com")

        def fake_request(method, url, **kwargs):
            assert kwargs["timeout"] == 5
            raise requests.exceptions.Timeout("请求超时")

        monkeypatch.setattr(client.session, "request", fake_request)

        try:
            with pytest.raises(requests.exceptions.Timeout, match="请求超时"):
                client.request("GET", "/products")
        finally:
            client.close()

        error_messages = [
            record.getMessage()
            for record in caplog.records
            if record.name == "common.api_client" and record.levelno == logging.ERROR
        ]
        assert len(error_messages) == 1
        assert "type=Timeout" in error_messages[0]
        assert "elapsed_ms=" in error_messages[0]
        assert "status=" not in error_messages[0]
