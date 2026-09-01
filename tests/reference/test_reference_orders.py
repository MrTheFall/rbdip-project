"""Baseline behavior tests. Do not edit — these describe externally
observable behavior that must survive every refactoring step."""
from app.db import db
from app.models import Product


def _create_product(client, name="Clean Code", price="45.00"):
    resp = client.post("/products", json={"name": name, "price": price})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def test_create_order_happy_path(client):
    product_id = _create_product(client)

    resp = client.post(
        "/orders",
        json={
            "customer_full_name": "Ada Lovelace",
            "customer_address": "1 Analytical Engine Way",
            "items": [{"product_id": product_id, "quantity": 2}],
        },
    )

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["status"] == "new"


def test_create_order_requires_customer_name(client):
    product_id = _create_product(client)

    resp = client.post(
        "/orders",
        json={
            "customer_address": "1 Analytical Engine Way",
            "items": [{"product_id": product_id, "quantity": 1}],
        },
    )

    assert resp.status_code == 400


def test_create_order_requires_at_least_one_item(client):
    resp = client.post(
        "/orders",
        json={
            "customer_full_name": "Ada Lovelace",
            "customer_address": "1 Analytical Engine Way",
            "items": [],
        },
    )

    assert resp.status_code == 400


def test_list_orders_includes_items(client):
    product_id = _create_product(client, name="Refactoring", price="50.00")
    client.post(
        "/orders",
        json={
            "customer_full_name": "Martin Fowler",
            "customer_address": "1 Pattern Street",
            "items": [{"product_id": product_id, "quantity": 3}],
        },
    )

    resp = client.get("/orders")
    assert resp.status_code == 200
    orders = resp.get_json()
    assert len(orders) == 1
    assert orders[0]["customer_full_name"] == "Martin Fowler"
    assert orders[0]["items"][0]["quantity"] == 3
