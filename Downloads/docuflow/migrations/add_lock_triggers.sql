-- DB-layer locking trigger for all six lockable document tables.
-- This is the second lock layer — the app layer is LockableMixin.ensure_editable().
-- This trigger fires BEFORE UPDATE and rejects ANY update where locked_at IS NOT NULL,
-- regardless of what issued the UPDATE (raw SQL, a bad migration, anything).
--
-- VERIFICATION (required by spec):
--   After applying, connect via psql directly (bypassing Flask) and run:
--     UPDATE invoices SET notes = 'test' WHERE locked_at IS NOT NULL;
--   Expected: ERROR: cannot modify a finalized document (invoices id=<N>)
--     UPDATE invoices SET notes = 'test' WHERE locked_at IS NULL;
--   Expected: UPDATE <N> (succeeds)

CREATE OR REPLACE FUNCTION prevent_locked_document_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.locked_at IS NOT NULL THEN
        RAISE EXCEPTION 'cannot modify a finalized document (% id=%)',
            TG_TABLE_NAME, OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all six lockable tables
DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['quotes','lpos','invoices','delivery_notes','credit_notes','debit_notes']
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_lock_%1$s ON %1$I;
             CREATE TRIGGER trg_lock_%1$s
             BEFORE UPDATE ON %1$I
             FOR EACH ROW EXECUTE FUNCTION prevent_locked_document_update();',
            t
        );
    END LOOP;
END;
$$;
