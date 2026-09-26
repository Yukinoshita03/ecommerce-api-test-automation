import pytest
from pathlib import Path

from common.read_yaml import load_yaml


def test_product_list(api_client):
    response = api_client.request("GET", "/products")

    assert response.status_code == 200, "商品列表请求失败"

    products = response.json()
    assert isinstance(products, list), "商品列表响应不是列表"

    for product in products:
        assert isinstance(product, dict), f"商品数据不是字典：{product}"
        assert "id" in product, f"商品缺少 id 字段：{product}"
        assert "name" in product, f"商品缺少 name 字段：{product}"
        assert "price" in product, f"商品缺少 price 字段：{product}"
        assert "stock" in product, f"商品缺少 stock 字段：{product}"


def test_product_detail(api_client):
    response = api_client.request("GET", "/products/1")

    assert response.status_code == 200, "商品详情请求失败"

    product = response.json()
    assert isinstance(product, dict), "商品详情响应不是字典"
    assert "id" in product, "商品详情缺少 id 字段"
    assert "name" in product, "商品详情缺少 name 字段"
    assert "price" in product, "商品详情缺少 price 字段"
    assert "stock" in product, "商品详情缺少 stock 字段"
    assert product["id"] == 1, "商品 ID 与预期不一致"
    assert isinstance(product["name"], str), "商品名称不是字符串"
    assert product["name"].strip(), "商品名称为空"


def test_product_not_found(api_client):
    response = api_client.request("GET", "/products/999999")

    assert response.status_code == 404, "不存在的商品应返回 404"
    assert response.json() == {
        "error": {
            "type": "http_error",
            "message": "Product not found",
        }
    }, "商品不存在时的错误响应不符合预期"


def test_product_post_missing_fields(api_client):
    response = api_client.request("POST", "/products", json={})

    assert response.status_code == 422, "缺少必填字段时应返回 422"

    body = response.json()
    assert isinstance(body, dict), "错误响应不是字典"
    assert "error" in body, "错误响应缺少 error 字段"
    assert body["error"]["type"] == "validation_error", "错误类型不符合预期"

    missing_fields = [
        item["loc"][-1]
        for item in body["error"]["details"]
        if item["type"] == "missing"
    ]
    assert {"name", "price", "stock"} <= set(missing_fields), (
        "错误详情没有指出所有缺失的必填字段"
    )


invalid_cases = load_yaml(
    Path(__file__).parent / "data" / "product_invalid_cases.yaml"
)

@pytest.mark.parametrize(
    "payload, expected_field",
    [
        (case["payload"], case["expected_field"])
        for case in invalid_cases
    ],
    ids=[case["case"] for case in invalid_cases],
)
def test_product_post_invalid_values(api_client, payload, expected_field):
    response = api_client.request("POST", "/products", json=payload)

    assert response.status_code == 422, "非法商品字段应返回 422"

    body = response.json()
    error_fields = [
        item["loc"][-1]
        for item in body["error"]["details"]
    ]
    assert expected_field in error_fields, f"错误详情未指出字段 {expected_field}"
