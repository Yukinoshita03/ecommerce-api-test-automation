class FailureAnalyzer:
    def __init__(self, client):
        self.client = client

    def analyze(self, context):
        result = self.client.analyze(context)

        if not isinstance(result, dict):
            raise ValueError("AI 分析结果必须是字典")

        required_fields = {
            "category": str,
            "summary": str,
            "hypotheses": list,
            "next_checks": list,
        }

        for field, expected_type in required_fields.items():
            if field not in result:
                raise ValueError(f"AI 分析结果缺少字段：{field}")

            if not isinstance(result[field], expected_type):
                raise ValueError(f"AI 分析字段类型错误：{field}")

        for index, hypothesis in enumerate(result["hypotheses"]):
            if not isinstance(hypothesis, dict):
                raise ValueError(f"hypotheses[{index}] 必须是字典")

            if not isinstance(hypothesis.get("cause"), str):
                raise ValueError(f"hypotheses[{index}].cause 必须是字符串")

            evidence = hypothesis.get("evidence")
            if not isinstance(evidence, list):
                raise ValueError(f"hypotheses[{index}].evidence 必须是列表")

            for item in evidence:
                if not isinstance(item, str):
                    raise ValueError(
                        f"hypotheses[{index}].evidence 中的元素必须是字符串"
                    )

        for index, suggestion in enumerate(result["next_checks"]):
            if not isinstance(suggestion, str):
                raise ValueError(f"next_checks[{index}] 必须是字符串")

        return result
