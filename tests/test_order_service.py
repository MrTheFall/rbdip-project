"""ЛР5: тесты ключевой логики заказов — валидация, сохранение, клиенты."""
import pytest

from app.models import Customer, Order, OrderItem
from app.services import calculate_order_total, split_customer_name


def _create_product(client, name="Clean Code", price="45.00"):
    resp = client.post("/products", json={"name": name, "price": price})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _order_payload(product_id, full_name="Ada Lovelace", **overrides):
    payload = {
        "customer_full_name": full_name,
        "customer_address": "1 Analytical Engine Way",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    payload.update(overrides)
    return payload


def test_list_products_returns_created_products(client):
    _create_product(client, name="Refactoring", price="50.00")

    resp = client.get("/products")

    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body) == 1
    assert body[0]["name"] == "Refactoring"
    assert body[0]["price"] == "50.00"


def test_missing_address_is_rejected(client):
    product_id = _create_product(client)
    payload = _order_payload(product_id)
    payload.pop("customer_address")

    resp = client.post("/orders", json=payload)

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "customer_address is required"


def test_unknown_product_is_rejected(client):
    resp = client.post(
        "/orders",
        json={
            "customer_full_name": "Ada Lovelace",
            "customer_address": "1 Analytical Engine Way",
            "items": [{"product_id": 9999, "quantity": 1}],
        },
    )

    assert resp.status_code == 400
    assert "not found" in resp.get_json()["error"]


@pytest.mark.parametrize("quantity", [0, -3])
def test_non_positive_quantity_is_rejected(client, quantity):
    product_id = _create_product(client)
    payload = _order_payload(product_id)
    payload["items"] = [{"product_id": product_id, "quantity": quantity}]

    resp = client.post("/orders", json=payload)

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "quantity must be positive"


def test_quantity_defaults_to_one(client):
    product_id = _create_product(client)
    payload = _order_payload(product_id)
    payload["items"] = [{"product_id": product_id}]

    assert client.post("/orders", json=payload).status_code == 201
    assert client.get("/orders").get_json()[0]["items"][0]["quantity"] == 1


def test_new_order_has_new_status(app, client):
    product_id = _create_product(client)
    client.post("/orders", json=_order_payload(product_id))

    with app.app_context():
        assert Order.query.one().status == "new"


def test_order_items_reference_products(app, client):
    product_id = _create_product(client, name="Refactoring", price="50.00")
    payload = _order_payload(product_id)
    payload["items"] = [{"product_id": product_id, "quantity": 3}]

    assert client.post("/orders", json=payload).status_code == 201

    with app.app_context():
        item = OrderItem.query.one()
        assert item.product_id == product_id
        assert item.quantity == 3


def test_repeat_customer_is_reused(app, client):
    product_id = _create_product(client)
    for _ in range(2):
        assert client.post("/orders", json=_order_payload(product_id)).status_code == 201

    with app.app_context():
        assert Customer.query.count() == 1
        assert Order.query.count() == 2
        customer = Customer.query.one()
        assert customer.first_name == "Ada"
        assert customer.last_name == "Lovelace"


def test_different_address_creates_new_customer(app, client):
    product_id = _create_product(client)
    client.post("/orders", json=_order_payload(product_id))
    client.post(
        "/orders",
        json=_order_payload(product_id, customer_address="2 Analytical Engine Way"),
    )

    with app.app_context():
        assert Customer.query.count() == 2


def test_order_total_uses_customer_type_and_coupon(client, capsys):
    product_id = _create_product(client, price="100.00")
    payload = _order_payload(product_id)
    payload["customer_type"] = "vip"
    payload["coupon_code"] = "SAVE10"

    assert client.post("/orders", json=payload).status_code == 201

    # 100 * 0.9 (vip) - 10 (SAVE10) = 80.0
    out = capsys.readouterr().out
    assert "for 80.0 has been placed" in out


def test_order_without_discounts_uses_regular_total(client, capsys):
    product_id = _create_product(client, price="10.00")
    payload = _order_payload(product_id)
    payload["items"] = [{"product_id": product_id, "quantity": 2}]

    assert client.post("/orders", json=payload).status_code == 201

    assert "for 20.0 has been placed" in capsys.readouterr().out


def test_calculate_order_total_delegates_to_calculator():
    items = [{"price": 10.0, "quantity": 2}]

    assert calculate_order_total(items) == 20.0
    assert calculate_order_total(items, "vip") == 18.0


def test_split_customer_name():
    assert split_customer_name("Ada Lovelace") == ("Ada", "Lovelace")
    assert split_customer_name("Cher") == ("Cher", None)
    assert split_customer_name("  Ada Lovelace  ") == ("Ada", "Lovelace")
    assert split_customer_name("Grace Brewster Hopper") == (
        "Grace",
        "Brewster Hopper",
    )
