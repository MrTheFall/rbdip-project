"""ЛР4: GET /orders не должен выполнять запрос на позиции каждого заказа."""
from sqlalchemy import event

from app.db import db

MAX_ALLOWED_SELECTS = 3


def _create_product(client, name="Domain-Driven Design", price="50.00"):
    resp = client.post("/products", json={"name": name, "price": price})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _create_order(client, product_id, items=2):
    payload = {
        "customer_full_name": "Test Customer",
        "customer_address": "Test Address",
        "items": [{"product_id": product_id, "quantity": 1} for _ in range(items)],
    }
    resp = client.post("/orders", json=payload)
    assert resp.status_code == 201


def _load_orders(app, client):
    """Returns the number of SELECTs issued by GET /orders and its payload."""
    statements = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", before_cursor_execute)
    try:
        response = client.get("/orders")
        assert response.status_code == 200
    finally:
        event.remove(db.engine, "before_cursor_execute", before_cursor_execute)
    return len(statements), response.get_json()


def test_listing_orders_uses_constant_number_of_queries(app, client):
    product_id = _create_product(client)

    _create_order(client, product_id)
    queries_one, orders_one = _load_orders(app, client)
    assert len(orders_one) == 1

    for _ in range(4):
        _create_order(client, product_id)
    queries_five, orders_five = _load_orders(app, client)

    assert queries_five >= 1, "счётчик запросов не сработал"
    assert len(orders_five) == 5, "joinedload задвоил заказы"
    assert queries_five == queries_one, (
        f"число запросов растёт с числом заказов: {queries_one} → {queries_five}"
    )
    assert queries_five <= MAX_ALLOWED_SELECTS, (
        f"GET /orders выполнил {queries_five} запросов при 5 заказах"
    )
