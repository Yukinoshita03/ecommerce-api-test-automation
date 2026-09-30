"""提取接口关联字段；匹配数量不符合预期时明确失败。"""

import allure
from jsonpath_ng import parse


def extract_one(body, expression):
    # 不附加提取值：表达式可能用于提取登录 token。
    with allure.step(f"JSONPath 提取单个字段：{expression}"):
        matches = parse(expression).find(body)
        assert len(matches) == 1, (
            f"JSONPath {expression} 应匹配 1 个值，实际匹配 {len(matches)} 个"
        )
        return matches[0].value
