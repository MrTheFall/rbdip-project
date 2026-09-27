import pytest

from app import create_app
from app.config import Config
from app.db import db


class TestConfig(Config):
    TESTING = True


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_tables(app):
    with app.app_context():
        db.session.execute(
            db.text(
                "TRUNCATE reviews, order_items, orders, customers, products "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.session.commit()
    yield
