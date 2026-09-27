import os
import pytest


@pytest.mark.skipif(
    not os.getenv("TEST_BASE_URL"),
    reason="没有配置 TEST_BASE_URL",
)
def test_skipif_demo():
    print("TEST_BASE_URL 已配置")
