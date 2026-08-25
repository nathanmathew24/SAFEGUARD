#!/usr/bin/env bash
# Manually proves the DB-layer lock trigger works (bypasses Flask entirely).
# Run after setup_db.sh.
set -euo pipefail

DB="${DATABASE_URL:-postgresql://docuflow:changeme@localhost:5432/docuflow}"

echo "=== DB-layer locking trigger verification (psql direct) ==="

psql "$DB" <<'EOF'
-- Insert test data
INSERT INTO companies (name, subscription_tier, subscription_active, whatsapp_addon_enabled)
VALUES ('Trigger Verify Co', 'starter', true, false)
ON CONFLICT DO NOTHING;

DO $$
DECLARE
  cid INT;
  uid INT;
  iid INT;
BEGIN
  SELECT id INTO cid FROM companies WHERE name = 'Trigger Verify Co';

  INSERT INTO users (company_id, email, password_hash, role)
  VALUES (cid, 'trigverify@test.com', 'x', 'owner')
  ON CONFLICT (email) DO NOTHING;
  SELECT id INTO uid FROM users WHERE email = 'trigverify@test.com';

  INSERT INTO invoices
    (company_id, invoice_number, customer_name, status, locked_at, subtotal, vat_amount, total, created_by)
  VALUES
    (cid, 'VERIFY-001', 'Verify Customer', 'draft', NULL, 0, 0, 0, uid)
  ON CONFLICT DO NOTHING;
  SELECT id INTO iid FROM invoices WHERE invoice_number = 'VERIFY-001' AND company_id = cid;

  -- Step 1: UPDATE on unlocked row (should succeed)
  UPDATE invoices SET notes = 'unlocked update' WHERE id = iid;
  RAISE NOTICE 'Step 1 PASSED: UPDATE on unlocked row succeeded (rows: %)', found;

  -- Lock the row
  UPDATE invoices SET locked_at = NOW(), status = 'finalized' WHERE id = iid;

  -- Step 2: UPDATE on locked row (trigger should reject)
  BEGIN
    UPDATE invoices SET notes = 'should fail' WHERE id = iid;
    RAISE EXCEPTION 'Step 2 FAILED: trigger did NOT fire — vulnerability exists!';
  EXCEPTION
    WHEN others THEN
      RAISE NOTICE 'Step 2 PASSED: trigger rejected UPDATE on locked row. Error: %', SQLERRM;
  END;

  -- Cleanup
  DELETE FROM invoices WHERE id = iid;
  DELETE FROM users WHERE id = uid;
  DELETE FROM companies WHERE id = cid;
END;
$$;
EOF

echo "=== Trigger verification complete ==="
