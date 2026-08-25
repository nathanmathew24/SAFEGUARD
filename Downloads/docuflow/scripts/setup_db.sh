#!/usr/bin/env bash
# One-shot DB setup: create tables, apply lock triggers, verify.
# Run from the docuflow/ directory.
set -euo pipefail

echo "=== DocuFlow DB Setup ==="

# 1. Run Flask-Migrate to create all tables
flask db init 2>/dev/null || true
flask db migrate -m "initial schema"
flask db upgrade

echo "--- Tables created ---"
psql "$DATABASE_URL" -c "\dt"

# 2. Apply the Postgres locking triggers
echo "--- Applying locking triggers ---"
psql "$DATABASE_URL" -f migrations/add_lock_triggers.sql

# 3. Verify triggers exist
echo "--- Trigger verification ---"
psql "$DATABASE_URL" -c "
SELECT trigger_name, event_object_table
FROM information_schema.triggers
WHERE trigger_name LIKE 'trg_lock_%'
ORDER BY event_object_table;
"

echo "=== Setup complete ==="
echo "Run: TEST_DATABASE_URL=\$DATABASE_URL pytest tests/ -v"
