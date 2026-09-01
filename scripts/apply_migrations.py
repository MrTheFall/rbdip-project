"""Apply pending SQL migrations from migrations/ to the database in
DATABASE_URL, in filename order, tracking what was already applied in a
schema_migrations table. Files are named NNNN_description.sql.
"""
import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://bookstore:bookstore@localhost:5432/bookstore",
).replace("postgresql+psycopg2://", "postgresql://")


def main():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute("SELECT filename FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found in migrations/")
        return

    for path in migration_files:
        if path.name in applied:
            print(f"skip (already applied): {path.name}")
            continue
        sql = path.read_text(encoding="utf-8")
        print(f"applying: {path.name}")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (path.name,),
            )

    conn.close()
    print("Migrations applied successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Migration failed: {exc}", file=sys.stderr)
        sys.exit(1)
