"""真正失败的 pytest 阶段才进入分析；模型故障不改变测试报告。"""
import json
import logging
import os

import allure

from common.ai.analyzer import FailureAnalyzer
from common.ai.client import FakeAIClient, OpenAICompatibleClient
from common.failure_context import sanitize_context

logger = logging.getLogger(__name__)


def analyze_failed_test(context):
    mode = os.getenv("AI_ANALYSIS_MODE", "off").lower()
    if mode == "off":
        return None

    try:
        if mode == "fake":
            client = FakeAIClient()
        elif mode == "real":
            client = OpenAICompatibleClient.from_env()
        else:
            raise ValueError("AI_ANALYSIS_MODE 只支持 off、fake、real")
        result = FailureAnalyzer(client).analyze(sanitize_context(context))
        analysis = {
            "status": "available",
            "mode": mode,
            "source": "pytest_failure",
            "phase": context["phase"],
            "analysis": sanitize_context(result),
        }
        name = f"AI 分析结果 ({context['phase']})"
    except Exception as error:
        logger.warning("AI 分析不可用：type=%s", type(error).__name__)
        analysis = {
            "status": "unavailable",
            "mode": mode,
            "source": "pytest_failure",
            "phase": context["phase"],
            "error_type": type(error).__name__,
            "message": "保留原测试结果和失败证据，模型分析未完成",
        }
        name = f"AI 分析不可用 ({context['phase']})"

    # 不通过公共证据入口记录，避免分析结果又进入下一个失败阶段的输入。
    allure.attach(json.dumps(analysis, ensure_ascii=False, indent=2), name=name,
                  attachment_type=allure.attachment_type.JSON)
    return analysis
