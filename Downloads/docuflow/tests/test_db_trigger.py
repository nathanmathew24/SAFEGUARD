"""
DB-layer locking trigger verification.

Connects to Postgres DIRECTLY via psycopg2 (bypassing Flask entirely)
and proves that the trigger rejects UPDATE on a locked row.

This test must pass after running:
  psql $TEST_DATABASE_URL < migrations/add_lock_triggers.sql

Run with:
  TEST_DATABASE_URL=postgresql://... pytest tests/test_db_trigger.py -v
"""
import os
import pytest

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


@pytest.mark.skipif(not PSYCOPG2_AVAILABLE, reason="psycopg2 not installed")
def test_db_trigger_rejects_update_on_locked_row(app):
    """
    1. Insert a row with locked_at = NULL (unlocked) — UPDATE should succeed.
    2. Set locked_at = NOW() — subsequent UPDATE should be REJECTED by trigger.
    """
    db_url = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://docuflow:changeme@localhost:5432/docuflow_test",
    )

    with psycopg2.connect(db_url) as conn:
        conn.autocommit = False
        cur = conn.cursor()

        # Insert minimal company and user for FK constraints
        cur.execute("""
            INSERT INTO companies (name, subscription_tier, subscription_active, whatsapp_addon_enabled)
            VALUES ('Trigger Test Co', 'starter', true, false)
            RETURNING id
        """)
        company_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO users (company_id, email, password_hash, role)
            VALUES (%s, 'trigger@test.com', 'x', 'owner')
            RETURNING id
        """, (company_id,))
        user_id = cur.fetchone()[0]

        # Insert an unlocked invoice
        cur.execute("""
            INSERT INTO invoices
              (company_id, invoice_number, customer_name, status, locked_at,
               subtotal, vat_amount, total, created_by)
            VALUES
              (%s, 'TRIG-001', 'Trigger Customer', 'draft', NULL,
               0, 0, 0, %s)
            RETURNING id
        """, (company_id, user_id))
        invoice_id = cur.fetchone()[0]

        # Step 1: UPDATE on unlocked row — should succeed
        cur.execute("UPDATE invoices SET notes = 'update1' WHERE id = %s", (invoice_id,))
        assert cur.rowcount == 1, "UPDATE on unlocked row should succeed"

        # Lock the row
        cur.execute(
            "UPDATE invoices SET locked_at = NOW(), status = 'finalized' WHERE id = %s",
            (invoice_id,)
        )

        # Step 2: UPDATE on locked row — trigger must reject it
        with pytest.raises(psycopg2.errors.RaiseException) as exc_info:
            cur.execute("UPDATE invoices SET notes = 'attempt after lock' WHERE id = %s", (invoice_id,))

        assert "finalized" in str(exc_info.value).lower() or "locked" in str(exc_info.value).lower()

        conn.rollback()  # clean up
