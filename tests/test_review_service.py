"""ЛР5: юнит-тесты сервиса отзывов (без HTTP-слоя)."""
from app.db import db
from app.models import Product
from app.review.models import Review
from app.review.service import ReviewService


def _product(name):
    product = Product(name=name, price=10)
    db.session.add(product)
    db.session.commit()
    return product


def test_add_and_list_reviews_by_product(app):
    with app.app_context():
        first = _product("Clean Code")
        second = _product("Refactoring")
        service = ReviewService()

        created = service.add_review(first.id, "Ada", 5, "Great")
        service.add_review(second.id, "Bob", 4, None)

        assert created.id is not None
        assert Review.query.count() == 2
        listed = service.list_reviews(first.id)
        assert [(r.author_name, r.rating, r.comment) for r in listed] == [
            ("Ada", 5, "Great")
        ]


def test_list_reviews_for_unknown_product_is_empty(app):
    with app.app_context():
        assert ReviewService().list_reviews(12345) == []
