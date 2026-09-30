import allure
import pytest

from common.jsonpath_utils import extract_one


@allure.feature("JSONPath 接口关联")
@allure.title("提取关联字段：{expression}")
@pytest.mark.parametrize(
    "body, expression, expected",
    [
        ({"id": 101}, "$.id", 101),
        ({"items": [{"product": {"id": 7}}]}, "$.items[0].product.id", 7),
        ({"access_token": "fake-token"}, "$.access_token", "fake-token"),
    ],
)
def test_extract_one_returns_value(body, expression, expected):
    assert extract_one(body, expression) == expected


@allure.feature("JSONPath 接口关联")
@allure.title("关联字段缺失或匹配多个值时明确失败")
@pytest.mark.parametrize("body, count", [({}, 0), ({"ids": [1, 2]}, 2)])
def test_extract_one_rejects_ambiguous_matches(body, count):
    expression = "$.id" if count == 0 else "$.ids[*]"
    with pytest.raises(AssertionError, match=f"实际匹配 {count} 个"):
        extract_one(body, expression)
