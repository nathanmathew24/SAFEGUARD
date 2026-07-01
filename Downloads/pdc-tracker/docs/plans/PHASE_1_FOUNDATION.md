# Phase 1 — Foundation Plan
**Project:** DocFlow — UAE Document Intelligence & Payment Management System  
**Owner:** Farzeel Fazir / Funoon.ai  
**Date:** 2026-07-01  
**Status:** AWAITING APPROVAL — no code written yet

---

## 1. What We Are Building

Phase 1 establishes the complete foundation that every later phase depends on. Nothing domain-specific (documents, PDCs, AI) is touched. The deliverables are:

| Deliverable | Description |
|---|---|
| Flask app factory | `create_app()` pattern, environment-aware config, Docker-ready |
| PostgreSQL + Alembic | DB connection, first migration, reversible schema |
| JWT Auth system | Access token (15 min) + refresh token (7 days) with rotation |
| RBAC | 4 roles enforced on every endpoint via decorator |
| Models | `User`, `Company`, `AuditLog` |
| Audit log | Append-only, logs every mutation with user/IP/timestamp |
| Health check | `GET /health` — unauthenticated, returns DB status |
| Security baseline | bcrypt cost=12, rate limiting, consistent error format, no stack traces |

This is the **security perimeter**. If Phase 1 is weak, the whole product is weak.

---

## 2. Acceptance Criteria

Each item must be true before Phase 1 is considered done.

### 2.1 Project Scaffold
- [ ] `create_app()` factory pattern implemented
- [ ] Config loads from environment variables — no hardcoded values
- [ ] `docker-compose up --build` starts the app and connects to PostgreSQL with no manual steps
- [ ] `flask db upgrade` applies the initial migration cleanly
- [ ] `flask db downgrade` reverses the migration without error
- [ ] `.env.example` committed with all required placeholder keys (no real secrets)
- [ ] `.env` is in `.gitignore`
- [ ] Directory structure matches CLAUDE.md exactly (`/app/agents`, `/app/api`, `/app/models`, `/app/services`, `/app/utils`, `/app/templates`, `/tests`, `/migrations`, `/docs`)

### 2.2 Authentication
- [ ] `POST /api/auth/register` creates a user; password stored as bcrypt hash (cost=12)
- [ ] `POST /api/auth/login` returns `access_token` (15 min TTY) and `refresh_token` (7 days TTY)
- [ ] `POST /api/auth/refresh` issues a new access token; rotates the refresh token (old token invalidated)
- [ ] `POST /api/auth/logout` invalidates the refresh token server-side
- [ ] Expired access tokens are rejected with `401`
- [ ] Invalid/tampered tokens are rejected with `401`
- [ ] Used refresh tokens (after rotation) are rejected with `401` (replay prevention)
- [ ] Rate limit on auth endpoints: 10 req/min per IP
- [ ] Plaintext passwords never appear in logs, responses, or database

### 2.3 RBAC
- [ ] Four roles exist: `owner`, `finance_manager`, `operations_staff`, `viewer`
- [ ] A `@require_role(*roles)` decorator enforces role on any endpoint
- [ ] Calling an endpoint with insufficient role returns `403` with consistent error body
- [ ] Calling an endpoint without a token returns `401`
- [ ] Role is encoded in JWT claims and verified server-side on every request (not trusted from request body)
- [ ] Owner role has access to all endpoints
- [ ] Viewer role is read-only — any write endpoint returns `403`

### 2.4 Models
- [ ] `Company` model: id, name, trade_license_no, trn (UAE Tax Registration Number), address, created_at, updated_at
- [ ] `User` model: id, company_id (FK), email, password_hash, role (enum), is_active, created_at, updated_at, last_login_at
- [ ] `AuditLog` model: id, table_name, record_id, action (enum: CREATE/UPDATE/VOID/LOGIN/LOGOUT), old_values (JSONB), new_values (JSONB), user_id (FK nullable — for system actions), ip_address, timestamp (UTC)
- [ ] `RefreshToken` model: id, user_id (FK), token_hash, issued_at, expires_at, revoked_at (nullable), replaced_by (nullable FK to self)
- [ ] All FKs enforced at DB level
- [ ] All monetary fields would be INTEGER — none in Phase 1 models but constraint noted in code comment
- [ ] All timestamps in UTC
- [ ] Soft-delete fields (`is_deleted`, `deleted_at`, `deleted_by`) on `User` and `Company`

### 2.5 Audit Log
- [ ] Every `CREATE`, `UPDATE`, `VOID` on any model triggers an audit log entry automatically
- [ ] `AuditLog` table has no `UPDATE` or `DELETE` route, endpoint, or ORM method
- [ ] Login and logout events are logged
- [ ] Audit log entries include `ip_address` extracted from the real request (handles reverse proxy `X-Forwarded-For`)
- [ ] `GET /api/audit` returns audit log — accessible by `owner` role only

### 2.6 Health Check
- [ ] `GET /health` returns `200 OK` with `{"status": "ok", "db": "ok", "timestamp": "<utc>"}` when DB is reachable
- [ ] Returns `{"status": "degraded", "db": "error"}` with `503` when DB is unreachable
- [ ] Endpoint requires no authentication

### 2.7 Security Baseline
- [ ] All API error responses use consistent format: `{"error": {"code": "...", "message": "..."}}`
- [ ] No stack traces or internal paths in any API response
- [ ] Rate limiting active: 100 req/min per user on general endpoints, 10 req/min on auth endpoints
- [ ] `bandit -r app/` reports zero HIGH severity findings
- [ ] `pip-audit` reports zero CRITICAL CVEs
- [ ] All packages pinned with exact versions in `requirements.txt`

### 2.8 Tests
- [ ] Test coverage on new Phase 1 code ≥ 80%
- [ ] `pytest tests/ -v --cov=app --cov-report=term-missing` runs and passes with no errors

---

## 3. Test Plan

### 3.1 Auth Tests (`tests/test_auth.py`)
| Test | What it proves |
|---|---|
| `test_register_success` | User created, password hashed, response has no password field |
| `test_register_duplicate_email` | Returns 409, no duplicate user created |
| `test_register_weak_password` | Returns 422, password policy enforced |
| `test_login_success` | Returns access + refresh tokens, last_login_at updated |
| `test_login_wrong_password` | Returns 401 |
| `test_login_inactive_user` | Returns 403 |
| `test_access_token_expiry` | Expired token rejected with 401 |
| `test_token_tamper` | Modified JWT signature rejected with 401 |
| `test_refresh_rotation` | New access token issued, old refresh token invalidated |
| `test_refresh_replay` | Used refresh token rejected with 401 |
| `test_logout_invalidates_refresh` | Refresh after logout returns 401 |
| `test_auth_rate_limit` | 11th request to auth endpoint within 1 min returns 429 |

### 3.2 RBAC Tests (`tests/test_rbac.py`)
| Test | What it proves |
|---|---|
| `test_owner_can_access_audit_log` | 200 |
| `test_finance_manager_cannot_access_audit_log` | 403 |
| `test_operations_staff_cannot_access_audit_log` | 403 |
| `test_viewer_cannot_access_audit_log` | 403 |
| `test_no_token_returns_401` | 401 on protected endpoint |
| `test_expired_token_returns_401` | 401 on protected endpoint |
| `test_viewer_read_access` | Viewer can call read endpoints |
| `test_viewer_blocked_on_write` | 403 on any write endpoint |

### 3.3 Audit Log Tests (`tests/test_audit.py`)
| Test | What it proves |
|---|---|
| `test_audit_log_on_user_create` | Entry created with correct fields |
| `test_audit_log_on_user_update` | old_values and new_values both present |
| `test_audit_log_on_login` | LOGIN action logged with IP |
| `test_audit_log_on_logout` | LOGOUT action logged |
| `test_audit_log_no_delete_endpoint` | DELETE /api/audit returns 405 |
| `test_audit_log_no_update_endpoint` | PATCH /api/audit/{id} returns 405 |
| `test_audit_log_ip_from_proxy` | X-Forwarded-For header used for IP |

### 3.4 Health Tests (`tests/test_health.py`)
| Test | What it proves |
|---|---|
| `test_health_ok` | 200, db=ok, no auth required |
| `test_health_db_down` | 503, db=error (mock DB disconnected) |

### 3.5 Model Tests (`tests/test_models.py`)
| Test | What it proves |
|---|---|
| `test_user_password_not_plaintext` | password_hash field ≠ raw password |
| `test_soft_delete_user` | is_deleted=True, user not returned in active queries |
| `test_refresh_token_expiry` | Expired token marked correctly |
| `test_audit_log_append_only` | Attempt to call session.delete(audit_log_entry) raises exception |

---

## 4. Edge Cases

| Edge Case | Handling |
|---|---|
| Register with email that has different casing | Normalize to lowercase before store/compare |
| Login attempt on non-existent email | Return 401 (same message as wrong password — no user enumeration) |
| Refresh token used twice simultaneously (race condition) | First use invalidates token; second receives 401 |
| JWT with `role` claim removed or tampered | Signature check fails → 401 |
| Very long email or password input | Max length validation (email ≤ 254, password ≤ 128 chars) |
| IP extraction behind reverse proxy | Check `X-Forwarded-For` first, fall back to `remote_addr` |
| `X-Forwarded-For` with multiple IPs (proxy chain) | Take the first (leftmost) IP |
| DB connection drops mid-request | 500 caught, consistent error format returned, no stack trace exposed |
| Clock skew on JWT expiry | Use `leeway=0` — no tolerance, strict expiry |
| Concurrent requests rotating the same refresh token | DB-level unique constraint + select-for-update prevents double rotation |
| `GET /health` called when DB is partially available | Actively test with a `SELECT 1` query, not just connection pool status |
| Audit log write fails | Log to stderr + return 500 — never silently swallow audit failures |

---

## 5. Assumptions

1. **PostgreSQL only.** No SQLite fallback, even for tests. Tests run against a dedicated test DB (separate from dev DB) defined by `TEST_DATABASE_URL`.
2. **No email verification in Phase 1.** User is active immediately after registration. Email verification is a Phase 6+ concern.
3. **Single company per deployment in Phase 1.** Company is created via a seed/CLI command, not a self-serve registration. Multi-tenancy isolation is at the `company_id` FK level but not enforced via row-level security yet.
4. **WhatsApp not connected in Phase 1.** The reminder agent and notification sender are out of scope.
5. **No frontend in Phase 1.** All testing is via REST API (curl / pytest HTTP client).
6. **Rate limiting via Flask-Limiter with in-memory storage in development.** Redis-backed in production (configured by `RATELIMIT_STORAGE_URL` env var).
7. **HTTPS enforced at reverse proxy level** (nginx/Railway). Flask itself does not redirect HTTP→HTTPS, but `SESSION_COOKIE_SECURE=True` is set.
8. **`bcrypt` cost factor = 12** as specified. This adds ~300ms per login — acceptable for security.
9. **Refresh token stored as SHA-256 hash** in the DB — never the raw token value.
10. **`bandit` will flag bcrypt and JWT usage** as informational/low severity — these are expected and not blockers. HIGH severity findings are blockers.

---

## 6. File Structure to Be Created

```
pdc-tracker/                    ← repo root (rename to docflow later)
├── CLAUDE.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
├── config.py
├── app/
│   ├── __init__.py             ← create_app() factory
│   ├── extensions.py           ← db, migrate, limiter, bcrypt
│   ├── agents/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py             ← /api/auth/* endpoints
│   │   ├── audit.py            ← /api/audit endpoint
│   │   └── health.py           ← /health endpoint
│   ├── models/
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   └── audit_log.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     ← JWT issue/verify/rotate logic
│   │   └── audit_service.py    ← append-only write helper
│   └── utils/
│       ├── __init__.py
│       ├── rbac.py             ← @require_role decorator
│       ├── errors.py           ← consistent error response builder
│       └── ip.py               ← IP extraction from request
├── migrations/
│   └── versions/
│       └── 001_initial_schema.py
├── tests/
│   ├── conftest.py             ← pytest fixtures, test DB setup
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_rbac.py
│   ├── test_audit.py
│   └── test_models.py
└── docs/
    └── plans/
        └── PHASE_1_FOUNDATION.md   ← this file
```

---

## 7. Dependencies (to be pinned in requirements.txt)

| Package | Purpose |
|---|---|
| Flask | Web framework |
| Flask-SQLAlchemy | ORM |
| Flask-Migrate | Alembic wrapper |
| Flask-Limiter | Rate limiting |
| Flask-Bcrypt | bcrypt hashing |
| PyJWT | JWT encode/decode |
| psycopg2-binary | PostgreSQL driver |
| python-dotenv | .env loading |
| pytest | Test runner |
| pytest-cov | Coverage |
| pytest-flask | Flask test client |
| bandit | Security linter |
| pip-audit | Dependency CVE scanner |

No Celery, no Redis, no Claude API, no WhatsApp — those are later phases.

---

## 8. What Is Explicitly OUT OF SCOPE for Phase 1

- Document models (Invoice, PDC, etc.) — Phase 2
- AI extraction agent — Phase 3
- File upload — Phase 3
- WhatsApp notifications — Phase 4
- PDF generation — Phase 5
- Any frontend — Phase 6
- Accounting integrations (Tally/Zoho) — not in any phase

---

**Awaiting your approval before any code is written.**
