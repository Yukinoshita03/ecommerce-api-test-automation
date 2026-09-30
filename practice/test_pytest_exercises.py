from jsonpath_ng import parse


def test_extract_order_id():
    body = {
        "id": 101,
        "items": [
            {"product": {"id": 7}, "quantity": 2},
            {"product": {"id": 9}, "quantity": 1},
        ],
    }

    expression = parse("$.id")
    matches = expression.find(body)
    order_ids = [match.value for match in matches]

    print(order_ids)
    assert order_ids == [101]
