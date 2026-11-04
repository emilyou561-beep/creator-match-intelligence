# SQLite Setup

From the project directory, create the database with:

```bash
python3 scripts/setup_database.py
```

The script creates `database/creator_matching.db`, converts blank CSV cells to SQL `NULL`, imports all seven tables, and checks foreign-key integrity.

Run the learning queries:

```bash
sqlite3 -header -column database/creator_matching.db < sql/02_basic_queries.sql
```

Run data-quality checks:

```bash
sqlite3 -header -column database/creator_matching.db < sql/03_data_quality_checks.sql
```

The database file is reproducible and excluded from Git. Commit the schema, import script, queries, and synthetic CSV files instead.
