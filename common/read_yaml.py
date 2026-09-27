from pathlib import Path

import yaml


def load_yaml(path):
    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_yaml_cases(path):
    """读取并检查字段错误用例，再交给 pytest 参数化。"""
    path = Path(path)
    try:
        cases = load_yaml(path)
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: YAML 语法错误：{exc}") from exc

    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{path}: 用例数据必须是非空列表")

    seen_ids = set()
    for index, case in enumerate(cases, start=1):
        location = f"{path}: 第 {index} 条"
        if not isinstance(case, dict):
            raise ValueError(f"{location}: 用例必须是字典")

        case_id = case.get("case")
        if isinstance(case_id, str) and case_id.strip():
            location += f" [{case_id}]"

        for field in ("case", "payload", "expected_field"):
            if field not in case:
                raise ValueError(f"{location}: 缺少 {field}")

        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{location}: case 必须是非空字符串")
        if not isinstance(case["payload"], dict):
            raise ValueError(f"{location}: payload 必须是字典")
        expected_field = case["expected_field"]
        if not isinstance(expected_field, str) or not expected_field.strip():
            raise ValueError(f"{location}: expected_field 必须是非空字符串")
        if case_id in seen_ids:
            raise ValueError(f"{location}: case 编号重复")
        seen_ids.add(case_id)

    return cases
