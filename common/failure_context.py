"""一次测试内的证据收集，供失败 Hook 使用；不保存原始凭据。"""
from contextvars import ContextVar
import re

from common.allure_reporting import redact

_current = ContextVar("failure_evidence", default=None)


def start_context():
    return _current.set({"events": [], "secrets": set()})


def finish_context(token):
    _current.reset(token)


def _find_secrets(value):
    from common.allure_reporting import SENSITIVE_KEYS
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS and isinstance(item, str) and item:
                yield item
            else:
                yield from _find_secrets(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _find_secrets(item)


def record_evidence(name, value):
    state = _current.get()
    if state is not None:
        state["secrets"].update(_find_secrets(value))
        state["events"].append({"name": name, "data": redact(value)})


def sanitize_text(text):
    state = _current.get()
    text = str(text)
    if state:
        for secret in sorted(state["secrets"], key=len, reverse=True):
            text = text.replace(secret, "***")
    text = re.sub(r"(?i)Bearer\s+[^\s,;\"']+", "Bearer ***", text)
    return text


def _sanitize_values(value):
    if isinstance(value, dict):
        return {key: _sanitize_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_values(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def sanitize_context(value):
    """隐藏字段凭据及本次测试中已识别的凭据文本。"""
    return _sanitize_values(redact(value))


def build_failure_context(report, call, item=None):
    state = _current.get()
    error = call.excinfo
    context = {
        "test_name": sanitize_text(report.nodeid),
        "phase": report.when,
        "outcome": report.outcome,
        "duration_seconds": report.duration,
        "exception_type": error.type.__name__ if error else None,
        # 不复制 traceback 源码或局部变量，避免带入凭据。
        "assertion_message": sanitize_text(error.value) if error else "",
        "evidence": _sanitize_values(state["events"]) if state else [],
        "logs": sanitize_text(report.caplog),
    }

    if item is not None:
        marker = item.get_closest_marker("analysis_context")
        if marker is not None:
            context["test_metadata"] = sanitize_context(dict(marker.kwargs))
    return context
