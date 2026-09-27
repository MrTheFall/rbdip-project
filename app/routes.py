from flask import Blueprint, jsonify, request

from app.db import db
from app.models import Order, OrderItem, Product, Review
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
    orders = Order.query.all()
    result = []
    for order in orders:
        # Each iteration issues a separate query for the order's items
        # instead of loading them together with the orders in one go.
        items = OrderItem.query.filter_by(order_id=order.id).all()
        result.append(
            {
                "id": order.id,
                "customer_full_name": order.customer.full_name,
                "status": order.status,
                "items": [
                    {"product_name": i.product.name, "quantity": i.quantity}
                    for i in items
                ],
            }
        )
    return jsonify(result)


@bp.route("/products/<int:product_id>/reviews", methods=["POST"])
def add_review(product_id):
    data = request.get_json(force=True)
    review = Review(
        product_id=product_id,
        author_name=data.get("author_name", "anonymous"),
        rating=data["rating"],
        comment=data.get("comment"),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({"id": review.id}), 201


@bp.route("/products/<int:product_id>/reviews", methods=["GET"])
def list_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id).all()
    return jsonify(
        [
            {"author_name": r.author_name, "rating": r.rating, "comment": r.comment}
            for r in reviews
        ]
    )
