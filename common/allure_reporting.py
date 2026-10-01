"""记录接口证据，递归隐藏凭据；不改变请求和响应。"""
import json
import allure

SENSITIVE_KEYS = {"password", "access_token", "refresh_token", "token", "authorization", "cookie", "set-cookie", "secret", "api_key", "x-api-key"}

def redact(value):
    if isinstance(value, dict):
        return {key: "***" if str(key).lower() in SENSITIVE_KEYS else redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value

def attach_json(name, value):
    from common.failure_context import record_evidence
    record_evidence(name, value)
    allure.attach(json.dumps(redact(value), ensure_ascii=False, indent=2, default=str), name=name, attachment_type=allure.attachment_type.JSON)

def attach_response(response):
    evidence = {"status_code": response.status_code}
    try:
        evidence["body"] = response.json()
    except ValueError:
        evidence["body"] = "非 JSON 响应，正文未记录"
    attach_json("接口响应", evidence)
