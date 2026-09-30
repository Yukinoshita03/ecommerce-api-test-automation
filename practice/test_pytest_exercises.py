import allure
import os

import pytest


def get_total(order):
    if "total" not in order:
        raise ValueError("订单缺少金额")
    return order["total"]


@allure.feature('pytest 基础练习')
@allure.title('缺少订单金额时抛出 ValueError')
def test_missing_total_raises_value_error():
    with allure.step("执行场景并检查预期结果"):
        with pytest.raises(ValueError, match="订单缺少金额"):
            get_total({"id": "ORD-2002"})


def get_base_url():
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


@allure.feature('pytest 基础练习')
@allure.title('临时环境变量覆盖默认地址')
def test_env_overrides_default(monkeypatch):
    with allure.step("执行场景并检查预期结果"):
        monkeypatch.setenv("TEST_BASE_URL", "http://qa.example")

        assert get_base_url() == "http://qa.example"
