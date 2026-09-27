import os

import pytest


def get_total(order):
    if "total" not in order:
        raise ValueError("订单缺少金额")
    return order["total"]


def test_missing_total_raises_value_error():
    with pytest.raises(ValueError, match="订单缺少金额"):
        get_total({"id": "ORD-2002"})


def get_base_url():
    return os.getenv("TEST_BASE_URL", "http://localhost:8000")


def test_env_overrides_default(monkeypatch):
    monkeypatch.setenv("TEST_BASE_URL", "http://qa.example")

    assert get_base_url() == "http://qa.example"
