import allure
import os
import pytest


@pytest.mark.skipif(
    not os.getenv("TEST_BASE_URL"),
    reason="没有配置 TEST_BASE_URL",
)
@allure.feature('pytest 跳过练习')
@allure.title('未配置环境变量时跳过练习')
def test_skipif_demo():
    with allure.step("执行场景并检查预期结果"):
        print("TEST_BASE_URL 已配置")
