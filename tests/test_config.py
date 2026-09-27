import pytest

from common.config import resolve_base_url


def test_base_url_uses_default_when_unset():
    assert resolve_base_url() == "http://localhost:8000"


def test_base_url_uses_environment_when_cli_is_unset():
    assert resolve_base_url(env_value="http://127.0.0.1:8001") == (
        "http://127.0.0.1:8001"
    )


def test_base_url_cli_overrides_environment():
    assert resolve_base_url(
        cli_value="http://localhost:8000",
        env_value="http://127.0.0.1:9",
    ) == "http://localhost:8000"


@pytest.mark.parametrize("value", ["", "  ", "localhost:8000", "ftp://localhost"])
def test_base_url_rejects_empty_or_non_http_address(value):
    with pytest.raises(ValueError, match="地址"):
        resolve_base_url(env_value=value)
