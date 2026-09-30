import allure
import pytest

from common.read_yaml import load_yaml_cases


@allure.feature('YAML 数据校验')
@allure.title('读取合法 YAML 用例')
def test_load_yaml_cases_accepts_valid_cases(tmp_path):
    with allure.step("执行场景并检查预期结果"):
        path = tmp_path / "cases.yaml"
        path.write_text(
            "- case: missing_price\n"
            "  payload: {}\n"
            "  expected_field: price\n",
            encoding="utf-8",
        )

        assert load_yaml_cases(path) == [
            {"case": "missing_price", "payload": {}, "expected_field": "price"}
        ]


@pytest.mark.parametrize(
    "contents, location, problem",
    [
        pytest.param(
            "- case: valid_case\n  payload: {}\n  expected_field: stock\n"
            "- case: bad_price\n  payload: {}\n",
            "第 2 条 [bad_price]",
            "缺少 expected_field",
            id="missing-field",
        ),
        pytest.param(
            "- payload: {}\n  expected_field: price\n",
            "第 1 条",
            "缺少 case",
            id="missing-case-id",
        ),
        pytest.param(
            "- case: bad_price\n  payload: []\n  expected_field: price\n",
            "第 1 条 [bad_price]",
            "payload 必须是字典",
            id="wrong-payload-type",
        ),
        pytest.param(
            "- case: duplicate\n  payload: {}\n  expected_field: price\n"
            "- case: duplicate\n  payload: {}\n  expected_field: stock\n",
            "第 2 条 [duplicate]",
            "case 编号重复",
            id="duplicate-case-id",
        ),
        pytest.param(
            "case: bad_price\npayload: {}\nexpected_field: price\n",
            "",
            "用例数据必须是非空列表",
            id="top-level-not-list",
        ),
        pytest.param(
            "[]\n",
            "",
            "用例数据必须是非空列表",
            id="empty-list",
        ),
        pytest.param(
            "- case: [\n",
            "",
            "YAML 语法错误",
            id="invalid-yaml",
        ),
    ],
)
@allure.feature('YAML 数据校验')
@allure.title('YAML 错误包含位置及原因：{problem}')
def test_load_yaml_cases_reports_location(tmp_path, contents, location, problem):
    with allure.step("执行场景并检查预期结果"):
        path = tmp_path / "cases.yaml"
        path.write_text(contents, encoding="utf-8")

        with pytest.raises(ValueError) as error:
            load_yaml_cases(path)

        message = str(error.value)
        assert str(path) in message
        assert location in message
        assert problem in message
