"""ЛР3: изменение схемы без простоя.

Expand-миграция 0003 только добавляет колонки, поэтому её переживают обе версии
приложения. Здесь проверяем более опасный шаг — contract 0004: он удаляет
старую колонку full_name, пока приложение продолжает обслуживать запросы.
"""
import threading
import time
from pathlib import Path

import psycopg2

from app.config import Config
from app.db import db
from app.models import Customer

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
CONTRACT_MIGRATION = MIGRATIONS_DIR / "0004_contract_drop_full_name.sql"


def _psycopg2_url():
    return Config.SQLALCHEMY_DATABASE_URI.replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def _create_product(client, name="Load Test Book", price="10.00"):
    resp = client.post("/products", json={"name": name, "price": price})
    assert resp.status_code == 201
    return resp.get_json()["id"]


def _order_payload(product_id, full_name="Ada Lovelace"):
    return {
        "customer_full_name": full_name,
        "customer_address": "1 Analytical Engine Way",
        "items": [{"product_id": product_id, "quantity": 1}],
    }


def _restore_pre_contract_state(app):
    """Возвращает схему к состоянию между expand и contract."""
    with app.app_context():
        db.session.execute(
            db.text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS full_name VARCHAR(255)")
        )
        db.session.commit()


def _apply_contract_migration_under_lock(pause_seconds=0.3):
    """Применяет настоящую contract-миграцию, удерживая блокировку таблицы:
    так выглядит накат на большой таблице, когда окно миграции заметно."""
    connection = psycopg2.connect(_psycopg2_url())
    try:
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute("LOCK TABLE customers IN ACCESS EXCLUSIVE MODE")
            cursor.execute(CONTRACT_MIGRATION.read_text(encoding="utf-8"))
            time.sleep(pause_seconds)
        connection.commit()
    finally:
        connection.close()


def test_contract_migration_under_load_does_not_break_api(app, client):
    _restore_pre_contract_state(app)
    payload = _order_payload(_create_product(client))

    intervals = []
    statuses = []
    errors = []
    stop = threading.Event()
    window = {}

    def load():
        load_client = app.test_client()
        while not stop.is_set():
            started = time.monotonic()
            try:
                statuses.append(load_client.post("/orders", json=payload).status_code)
                statuses.append(load_client.get("/orders").status_code)
            except Exception as exc:  # фиксируем любые сбои транспорта
                errors.append(repr(exc))
            finally:
                intervals.append((started, time.monotonic()))
            time.sleep(0.005)

    worker = threading.Thread(target=load, daemon=True)
    worker.start()

    # Ждём, пока нагрузка реально раскрутится: на «холодном» старте первые
    # запросы медленные и иначе могут не попасть в окно миграции.
    deadline = time.monotonic() + 10
    while len(intervals) < 4 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert len(intervals) >= 4, "нагрузка не раскрутилась до начала миграции"

    window["start"] = time.monotonic()
    _apply_contract_migration_under_lock()
    window["end"] = time.monotonic()

    stop.set()
    worker.join(timeout=10)

    assert errors == [], f"во время миграции запросы падали: {errors[:3]}"
    assert statuses, "нагрузка не успела выполнить ни одного запроса"
    assert max(statuses) < 500, f"во время миграции были 5xx: {sorted(set(statuses))}"
    overlapped = [
        interval
        for interval in intervals
        if interval[0] <= window["end"] and interval[1] >= window["start"]
    ]
    assert overlapped, "нагрузка не пересеклась с окном миграции"


def test_customer_name_is_split_into_first_and_last(app, client):
    product_id = _create_product(client)
    assert client.post("/orders", json=_order_payload(product_id)).status_code == 201

    with app.app_context():
        customer = Customer.query.one()
        assert customer.first_name == "Ada"
        assert customer.last_name == "Lovelace"

    listed = client.get("/orders").get_json()
    assert listed[0]["customer_full_name"] == "Ada Lovelace"


def test_single_word_name_has_no_last_name(app, client):
    product_id = _create_product(client)
    client.post("/orders", json=_order_payload(product_id, full_name="Cher"))

    with app.app_context():
        customer = Customer.query.one()
        assert customer.first_name == "Cher"
        assert customer.last_name is None

    listed = client.get("/orders").get_json()
    assert listed[0]["customer_full_name"] == "Cher"


def test_customers_table_no_longer_has_full_name(app):
    with app.app_context():
        columns = {
            row[0]
            for row in db.session.execute(
                db.text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'customers'"
                )
            )
        }
    assert {"first_name", "last_name"} <= columns
    assert "full_name" not in columns
