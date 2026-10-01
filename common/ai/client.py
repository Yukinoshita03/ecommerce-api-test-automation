import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests

from common.allure_reporting import redact


class FakeAIClient:
    def analyze(self, context):
        return {
            "category": "assertion_mismatch",
            "summary": "模拟分析：断言结果与预期不一致",
            "hypotheses": [
                {
                    "cause": "测试预期或测试数据可能不一致",
                    "evidence": [
                        context["assertion_message"],
                    ],
                }
            ],
            "next_checks": [
                "核对测试数据和预期值",
            ],
        }


class AIClientError(RuntimeError):
    """模型服务不可用或响应格式错误；消息中不包含 Key 或响应正文。"""


class OpenAICompatibleClient:
    def __init__(self, endpoint, api_key, model, timeout=30):
        address = urlsplit(endpoint)
        if address.scheme not in {"http", "https"} or not address.hostname:
            raise ValueError("模型 endpoint 必须是完整 HTTP(S) 地址")
        if not api_key or not model:
            raise ValueError("必须配置模型 API Key 和模型名称")
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        return cls(
            endpoint=os.getenv("AI_ENDPOINT", ""),
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv("AI_MODEL", ""),
        )

    def analyze(self, context):
        # 传入的是失败收集器生成的上下文，不发送原始凭据和完整 traceback。
        context_text = json.dumps(redact(context), ensure_ascii=False)
        if len(context_text) > 24000:
            raise AIClientError("失败上下文超过 24000 字符，需先缩减证据")

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        Path(__file__).resolve().parent / "prompts" / "failure_analysis.txt"
                    ).read_text(encoding="utf-8"),
                },
                {"role": "user", "content": context_text},
            ],
        }
        # 使用独立请求，不经过被测业务 ApiClient，避免混入业务 JWT 和证据。
        try:
            response = requests.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise AIClientError(f"模型请求失败：{type(error).__name__}") from None

        if not 200 <= response.status_code < 300:
            raise AIClientError(f"模型接口返回 HTTP {response.status_code}")

        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (ValueError, KeyError, IndexError, TypeError):
            raise AIClientError("模型响应缺少有效的 JSON 分析内容") from None
        if not isinstance(result, dict):
            raise AIClientError("模型分析内容必须是 JSON 对象")
        return result
