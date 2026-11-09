from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from app.db import db
from app.models import Order, OrderItem, Product
from app.services import OrderService

bp = Blueprint("bookstore", __name__)


@bp.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True)
    product = Product(
        name=data["name"],
        price=data["price"],
        description=data.get("description"),
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({"id": product.id, "name": product.name}), 201


@bp.route("/products", methods=["GET"])
def list_products():
    products = Product.query.all()
    return jsonify(
        [{"id": p.id, "name": p.name, "price": str(p.price)} for p in products]
    )


@bp.route("/orders", methods=["POST"])
def create_order():
    payload = request.get_json(force=True)
    try:
        order = OrderService().create_order(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"id": order.id, "status": order.status}), 201


@bp.route("/orders", methods=["GET"])
def list_orders():
    # Eager-load the customer and the items with their products so the whole
    # response is built with a constant number of queries, not one per order.
    orders = (
        Order.query.options(
            joinedload(Order.customer),
            joinedload(Order.items).joinedload(OrderItem.product),
        ).all()
    )
    result = []
    for order in orders:
        result.append(
            {
                "id": order.id,
                "customer_full_name": order.customer.full_name,
                "status": order.status,
                "items": [
                    {"product_name": item.product.name, "quantity": item.quantity}
                    for item in order.items
                ],
            }
        )
    return jsonify(result)
