from uuid import uuid4

import pytest


def _create_test_product(client, stock):
    response = client.request(
        "POST",
        "/products",
        json={
            "name": f"order_test_{uuid4().hex}",
            "description": "独立的订单测试商品",
            "price": 10.0,
            "stock": stock,
        },
    )
    assert response.status_code == 201, f"创建测试商品失败：{response.text}"
    return response.json()


@pytest.mark.stateful
def test_create_order_from_cart(authenticated_client):
    product_id = _create_test_product(authenticated_client, stock=2)["id"]

    try:
        cart_response = authenticated_client.request(
            "POST", "/cart", json={"product_id": product_id, "quantity": 2}
        )
        assert cart_response.status_code == 201, (
            f"加入购物车失败：{cart_response.text}"
        )

        order_response = authenticated_client.request("POST", "/orders")
        assert order_response.status_code == 201, (
            f"创建订单失败：{order_response.text}"
        )
        created_order = order_response.json()
        order_id = created_order["id"]

        detail_response = authenticated_client.request("GET", f"/orders/{order_id}")
        assert detail_response.status_code == 200, "按 ID 查询订单失败"
        order = detail_response.json()
        assert order["id"] == order_id, "查回的订单 ID 不一致"
        assert order["status"] == "PENDING", "新订单状态应为 PENDING"
        assert order["total_price"] == 20.0, "订单总金额应为 10 × 2"
        assert len(order["items"]) == 1, "订单应只有一条商品明细"
        item = order["items"][0]
        assert item["product"]["id"] == product_id, "订单商品 ID 不一致"
        assert item["quantity"] == 2, "订单商品数量不正确"
        assert item["price_at_purchase"] == 10.0, "下单单价不正确"

        cart_after = authenticated_client.request("GET", "/cart")
        assert cart_after.status_code == 200, "下单后查询购物车失败"
        assert cart_after.json() == [], "下单成功后购物车应为空"

        product_after = authenticated_client.request("GET", f"/products/{product_id}")
        assert product_after.status_code == 200, "下单后查询商品失败"
        assert product_after.json()["stock"] == 0, "下单后应扣减 2 件库存"
    finally:
        # 失败时清空本次测试账号的购物车；商品和订单没有删除接口。
        authenticated_client.request("DELETE", "/cart")


@pytest.mark.stateful
def test_create_order_with_empty_cart(authenticated_client):
    cart_before = authenticated_client.request("GET", "/cart")
    assert cart_before.status_code == 200, "下单前查询购物车失败"
    assert cart_before.json() == [], "测试用户的购物车应为空"

    orders_before = authenticated_client.request("GET", "/orders")
    assert orders_before.status_code == 200, "下单前查询订单失败"
    assert orders_before.json() == [], "测试用户下单前不应有订单"

    response = authenticated_client.request("POST", "/orders")
    assert response.status_code == 400, "空购物车下单应返回 400"
    assert response.json() == {
        "error": {"type": "http_error", "message": "Cart is empty"}
    }, "空购物车错误响应不符合预期"

    orders_after = authenticated_client.request("GET", "/orders")
    assert orders_after.status_code == 200, "下单后查询订单失败"
    assert orders_after.json() == [], "空购物车下单不应创建订单"

    cart_after = authenticated_client.request("GET", "/cart")
    assert cart_after.status_code == 200, "下单后查询购物车失败"
    assert cart_after.json() == [], "失败的下单不应改变购物车"


@pytest.mark.stateful
def test_order_rejects_stale_cart_stock(
    authenticated_client, second_authenticated_client
):
    owner = authenticated_client
    other = second_authenticated_client
    owner_me = owner.request("GET", "/auth/me")
    other_me = other.request("GET", "/auth/me")
    assert owner_me.status_code == other_me.status_code == 200
    assert owner_me.json()["id"] != other_me.json()["id"], "两个用户必须相互独立"

    product = _create_test_product(owner, stock=1)
    product_id = product["id"]
    try:
        for client in (owner, other):
            add_response = client.request(
                "POST", "/cart", json={"product_id": product_id, "quantity": 1}
            )
            assert add_response.status_code == 201, (
                f"测试用户加购失败：{add_response.text}"
            )

        first_order = owner.request("POST", "/orders")
        assert first_order.status_code == 201, f"用户 A 下单失败：{first_order.text}"
        assert first_order.json()["items"][0]["product"]["id"] == product_id

        second_order = other.request("POST", "/orders")
        assert second_order.status_code == 400, "库存耗尽后用户 B 下单应返回 400"
        assert second_order.json() == {
            "error": {
                "type": "http_error",
                "message": f"Insufficient stock for {product['name']}",
            }
        }, "库存不足错误响应不符合预期"

        orders_after = other.request("GET", "/orders")
        assert orders_after.status_code == 200, "查询用户 B 的订单失败"
        assert orders_after.json() == [], "下单失败不应为用户 B 创建订单"

        cart_after = other.request("GET", "/cart")
        assert cart_after.status_code == 200, "查询用户 B 的购物车失败"
        assert len(cart_after.json()) == 1, "下单失败应保留用户 B 的购物车"
        assert cart_after.json()[0]["product"]["id"] == product_id
        assert cart_after.json()[0]["quantity"] == 1

        product_after = owner.request("GET", f"/products/{product_id}")
        assert product_after.status_code == 200, "查询商品库存失败"
        assert product_after.json()["stock"] == 0, "用户 B 下单失败不应再扣库存"
    finally:
        # 仅清理各自的购物车；商品和用户 A 的订单会留在测试库。
        owner.request("DELETE", "/cart")
        other.request("DELETE", "/cart")


@pytest.mark.stateful
def test_order_detail_is_hidden_from_other_user(
    authenticated_client, second_authenticated_client
):
    owner = authenticated_client
    other = second_authenticated_client
    product_id = _create_test_product(owner, stock=1)["id"]
    try:
        add_response = owner.request(
            "POST", "/cart", json={"product_id": product_id, "quantity": 1}
        )
        assert add_response.status_code == 201, f"用户 A 加购失败：{add_response.text}"

        created = owner.request("POST", "/orders")
        assert created.status_code == 201, f"用户 A 创建订单失败：{created.text}"
        order_id = created.json()["id"]

        owner_detail = owner.request("GET", f"/orders/{order_id}")
        assert owner_detail.status_code == 200, "订单所有者应能查询订单"
        assert owner_detail.json()["id"] == order_id

        other_detail = other.request("GET", f"/orders/{order_id}")
        assert other_detail.status_code == 404, "其他用户查询该订单应返回 404"
        assert other_detail.json() == {
            "error": {"type": "http_error", "message": "Order not found"}
        }, "其他用户不应获得订单详情"

        other_orders = other.request("GET", "/orders")
        assert other_orders.status_code == 200, "查询其他用户订单列表失败"
        assert other_orders.json() == [], "其他用户的订单列表不应出现该订单"
    finally:
        owner.request("DELETE", "/cart")
