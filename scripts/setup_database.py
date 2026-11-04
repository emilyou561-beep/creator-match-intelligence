"""Build a fresh SQLite database from the public synthetic CSV files."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "sample_data"
SCHEMA_FILE = PROJECT_DIR / "sql" / "01_schema.sql"
DATABASE_DIR = PROJECT_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "creator_matching.db"
TEMP_DATABASE_FILE = DATABASE_DIR / "creator_matching.tmp.db"

TABLES = {
    "creators": "creators.csv",
    "tags": "tags.csv",
    "creator_tags": "creator_tags.csv",
    "brand_collaborations": "brand_collaborations.csv",
    "risk_records": "risk_records.csv",
    "campaigns": "campaigns.csv",
    "campaign_tags": "campaign_tags.csv",
}


def read_csv(file_path: Path) -> tuple[list[str], list[list[str | None]]]:
    """Return headers and rows, converting blank CSV cells to SQL NULL."""
    with file_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        headers = reader.fieldnames
        if not headers:
            raise ValueError(f"Missing header row: {file_path}")
        rows = [
            [None if row[column] == "" else row[column] for column in headers]
            for row in reader
        ]
    return headers, rows


def insert_csv(connection: sqlite3.Connection, table: str, file_name: str) -> int:
    headers, rows = read_csv(DATA_DIR / file_name)
    columns = ", ".join(headers)
    placeholders = ", ".join("?" for _ in headers)
    connection.executemany(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", rows
    )
    return len(rows)


def main() -> None:
    DATABASE_DIR.mkdir(exist_ok=True)
    TEMP_DATABASE_FILE.unlink(missing_ok=True)

    row_counts: dict[str, int] = {}
    try:
        with sqlite3.connect(TEMP_DATABASE_FILE) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))

            for table, file_name in TABLES.items():
                row_counts[table] = insert_csv(connection, table, file_name)

            foreign_key_errors = connection.execute(
                "PRAGMA foreign_key_check"
            ).fetchall()
            if foreign_key_errors:
                raise ValueError(f"Foreign-key errors: {foreign_key_errors}")

        TEMP_DATABASE_FILE.replace(DATABASE_FILE)
    except Exception:
        TEMP_DATABASE_FILE.unlink(missing_ok=True)
        raise

    print(f"Created: {DATABASE_FILE}")
    for table, count in row_counts.items():
        print(f"  {table}: {count} rows")
    print("Foreign-key check: PASS")


if __name__ == "__main__":
    main()
