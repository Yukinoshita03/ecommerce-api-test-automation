import pytest


@pytest.mark.stateful
def test_cart_add_list_and_remove(authenticated_client):
    products_response = authenticated_client.request("GET", "/products")
    assert products_response.status_code == 200, "查询商品列表失败"

    products = products_response.json()
    product = next((item for item in products if item["stock"] >= 2), None)
    assert product is not None, "没有库存至少为 2 的商品可用于购物车测试"

    product_id = product["id"]
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
        # 每个测试使用独立账号；断言失败时也清空这个账号的购物车。
        authenticated_client.request("DELETE", "/cart")
