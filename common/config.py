from urllib.parse import urlsplit


DEFAULT_BASE_URL = "http://localhost:8000"


def resolve_base_url(cli_value=None, env_value=None):
    """命令行参数优先于环境变量，最后使用本地默认地址。"""
    value = cli_value if cli_value is not None else env_value
    if value is None:
        value = DEFAULT_BASE_URL
    if not isinstance(value, str) or not value.strip():
        raise ValueError("测试服务地址不能为空")

    value = value.strip()
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
    except ValueError as exc:
        raise ValueError(f"无效的测试服务地址：{value}") from exc
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError(f"测试服务地址必须是带主机名的 HTTP(S) URL：{value}")
    return value
