"""Install the bundled schema, reference data, and procedures in PostgreSQL.

Run with the backend dependencies installed. This is setup only: it never
generates contacts in Python. Reapplying the SQL preserves the reference IDs.
"""

import os
from pathlib import Path

import psycopg


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://faker:faker@localhost:5432/faker"
    )
    with psycopg.connect(database_url) as connection:
        for name in ("001_schema.sql", "002_lookup_data.sql", "003_procedures.sql", "004_markov.sql", "005_benchmark.sql"):
            source = root / "database" / name
            connection.execute(source.read_text(encoding="utf-8-sig"), prepare=False)
            print(f"Applied {source.relative_to(root)}")
    print("Database is ready.")


if __name__ == "__main__":
    main()
