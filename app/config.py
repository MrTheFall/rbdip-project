import os

DEFAULT_DATABASE_URL = "postgresql+psycopg2://bookstore:bookstore@localhost:5432/bookstore"


def _database_url():
    """Return the database URL with an explicit psycopg2 driver.

    Since SQLAlchemy 2.1 a bare "postgresql://" URL resolves to the psycopg
    (v3) driver, while the project installs psycopg2-binary. Spelling the
    driver out keeps both URL forms working.
    """
    url = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    return url.replace("postgresql://", "postgresql+psycopg2://", 1)


class Config:
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
