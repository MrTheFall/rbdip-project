from flask import Flask

from app.config import Config
from app.db import db


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)

    from app.routes import bp as bookstore_bp

    app.register_blueprint(bookstore_bp)

    return app
