import allure
import pytest

from common.config import resolve_base_url


@allure.feature('环境配置')
@allure.title('未配置时使用默认地址')
def test_base_url_uses_default_when_unset():
    with allure.step("执行场景并检查预期结果"):
        assert resolve_base_url() == "http://localhost:8000"


@allure.feature('环境配置')
@allure.title('使用环境变量地址')
def test_base_url_uses_environment_when_cli_is_unset():
    with allure.step("执行场景并检查预期结果"):
        assert resolve_base_url(env_value="http://127.0.0.1:8001") == (
            "http://127.0.0.1:8001"
        )


@allure.feature('环境配置')
@allure.title('命令行地址覆盖环境变量')
def test_base_url_cli_overrides_environment():
    with allure.step("执行场景并检查预期结果"):
        assert resolve_base_url(
            cli_value="http://localhost:8000",
            env_value="http://127.0.0.1:9",
        ) == "http://localhost:8000"


@pytest.mark.parametrize("value", ["", "  ", "localhost:8000", "ftp://localhost"])
@allure.feature('环境配置')
@allure.title('拒绝非法地址：{value}')
def test_base_url_rejects_empty_or_non_http_address(value):
    with allure.step("执行场景并检查预期结果"):
        with pytest.raises(ValueError, match="地址"):
            resolve_base_url(env_value=value)
