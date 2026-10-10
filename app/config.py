import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://bookstore:bookstore@localhost:5432/bookstore",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
