from flask import Blueprint, jsonify, request

from app.review.service import ReviewService

bp = Blueprint("review", __name__)


@bp.route("/products/<int:product_id>/reviews", methods=["POST"])
def add_review(product_id):
    data = request.get_json(force=True)
    review = ReviewService().add_review(
        product_id,
        data.get("author_name", "anonymous"),
        data["rating"],
        data.get("comment"),
    )
    return jsonify({"id": review.id}), 201


@bp.route("/products/<int:product_id>/reviews", methods=["GET"])
def list_reviews(product_id):
    reviews = ReviewService().list_reviews(product_id)
    return jsonify(
        [
            {"author_name": r.author_name, "rating": r.rating, "comment": r.comment}
            for r in reviews
        ]
    )
