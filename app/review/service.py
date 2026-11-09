from app.db import db
from app.review.models import Review


class ReviewService:
    """Adds and lists reviews without touching the order module."""

    def add_review(self, product_id, author_name, rating, comment):
        review = Review(
            product_id=product_id,
            author_name=author_name,
            rating=rating,
            comment=comment,
        )
        db.session.add(review)
        db.session.commit()
        return review

    def list_reviews(self, product_id):
        return Review.query.filter_by(product_id=product_id).all()
