from uuid import uuid4

import pytest


@pytest.mark.stateful
def test_cart_add_list_and_remove(authenticated_client):
    product_response = authenticated_client.request(
        "POST",
        "/products",
        json={
            "name": f"cart_test_{uuid4().hex}",
            "description": "独立的购物车测试商品",
            "price": 10.0,
            "stock": 2,
        },
    )
    assert product_response.status_code == 201, (
        f"创建购物车测试商品失败：{product_response.text}"
    )
    product_id = product_response.json()["id"]
    try:
        add_response = authenticated_client.request(
            "POST", "/cart", json={"product_id": product_id, "quantity": 2}
        )
        assert add_response.status_code == 201, "加入购物车失败"
        cart_item = add_response.json()
        cart_id = cart_item["id"]

        list_response = authenticated_client.request("GET", "/cart")
        assert list_response.status_code == 200, "查询购物车失败"
        cart_items = list_response.json()
        listed_item = next((item for item in cart_items if item["id"] == cart_id), None)
        assert listed_item is not None, "新加入的商品没有出现在购物车中"
        assert listed_item["quantity"] == 2, "购物车商品数量不正确"
        assert listed_item["product"]["id"] == product_id, "购物车商品 ID 不正确"

        delete_response = authenticated_client.request("DELETE", f"/cart/{cart_id}")
        assert delete_response.status_code == 200, "删除购物车商品失败"

        after_delete = authenticated_client.request("GET", "/cart")
        assert after_delete.status_code == 200, "删除后查询购物车失败"
        assert all(item["id"] != cart_id for item in after_delete.json()), (
            "删除后购物车中仍存在该商品"
        )
    finally:
        # 只清理本次测试账号的购物车；新建商品没有删除接口。
        authenticated_client.request("DELETE", "/cart")
