# TODO

## v3.2.0 — verification
- [x] Synchronize `main` and `develop` before local testing.
- [x] Update backend, sidebar, and service User-Agent version declarations to 3.2.0.
- [x] User-confirmed local application startup.
- [x] User-confirmed page smoke tests: Asset Management, Nessus Manual Scan, Nessus Scan Results, Threat Intelligence, Administration, Logs & Events.
- [ ] Capture `/api/info` version and schema output in release notes.
- [ ] Test Alembic current/history/upgrade using a backed-up test database.
- [ ] Test Nessus upload and analysis using a synthetic XML fixture.
- [ ] Verify finding state transitions, CVE validation, register deduplication, and host mapping.
- [ ] Test Telegram scan, source context retention, NVD-first multi-source enrichment, review, and promotion.
- [ ] Verify new CVE Program and GitHub Security Advisory feeds are automatically seeded, enabled, and individually testable.
- [ ] Test `CVE-2018-10388` end-to-end and confirm the CVE Program description/source reference is retrieved when NVD fields are unavailable.
- [ ] Test the new Scan Result → Details → `Refresh Sources` action on an existing partial/not-found finding.
- [ ] Verify feed disablement, NVD 429/503 retry behavior, updated API-key-aware pacing, GitHub anonymous pacing/token behavior, and retry of CVEs previously marked not found.
- [ ] Verify Remediation/Mitigation are manually maintained in Vulnerabilities and are not required by Scan Result enrichment.
- [ ] Test Jira issue creation using a non-production project and API token.
- [ ] Run automated/backend checks available in the repository and record exact results.

## v3.4.0 — automatic default admin and forced password change
- [ ] Back up a test database and verify Alembic migrations 0009 and 0010 on a populated schema 0008 database.
- [ ] Verify a clean database creates the users table and reports schema version 10.
- [ ] Verify automatic `admin` bootstrap creates a strong temporary password in ignored `backend/data/INITIAL_ADMIN_CREDENTIALS.txt` only when no users exist.
- [ ] Verify first login forces password change and removes the temporary credential file only after a successful change.
- [ ] Test valid/invalid login, logout, eight-hour session expiry, inactive-user rejection, and login throttling.
- [ ] Verify unauthenticated browser access is redirected to login/setup and unauthenticated API/docs access is rejected.
- [ ] Verify Admin can create/edit/reset/delete accounts and User cannot access the User Management API.
- [ ] Verify duplicate usernames are rejected and the last active administrator cannot be disabled, demoted, or deleted.
- [ ] Confirm HTTP-only and SameSite cookie attributes, TLS Secure behavior, and that session-signing key/database files remain outside Git.
- [ ] Review permissions for non-user-management application actions before production deployment; current User role only prevents access to user administration.

## v3.5.0 — Vulnerability Register custom fields and table layout
- [ ] Verify migration 0011 upgrades a backed-up schema-10 database and preserves existing Vulnerability Register records.
- [ ] Verify a fresh install stamps/creates schema 11 correctly.
- [ ] Test Admin-only custom field create, rename, required/show-in-table toggles, and delete.
- [ ] Test custom values on create/edit; test required-field validation and duplicate field-name rejection.
- [ ] Verify custom values appear under their dynamic table columns, and that deleting a field removes only its own stored values.
- [ ] Verify combined Affected Product / Version columns on Scan Result and Vulnerability Register.
- [ ] Verify prior table settings migrate visibility/width preferences correctly after merging the columns.
- [ ] Run backend tests and browser smoke tests; record actual outcomes before release.

## v3.6.0 — Scan Result asset matching
- [ ] Run `python -m unittest discover -s tests -p test_asset_message_matching.py` from the repository root.
- [ ] Verify matching against representative Equipment, Operating System, Application and Library records.
- [ ] Verify system identifiers (name/vendor/model/IP/serial/CPE/PURL) and custom asset field values cause the expected flags.
- [ ] Verify generic/common terms and substrings inside longer words do not cause obvious false positives.
- [ ] Verify Scan Result list, Details, edit/save, refresh-source and review-status changes preserve the asset match flag.
- [ ] Confirm matched rows are highlighted, the Asset Match column names matched inventory items, and the Details panel lists matching fields/terms.
- [ ] Confirm asset records added/edited after a scan are reflected on the next Scan Result refresh without a database migration.
- [ ] Record local backend/browser results; do not treat the heuristic as a definitive asset applicability result.

## Customer deployment
- [ ] Define supported OS and Python version.
- [ ] Create a clean package excluding local database, credentials, virtual environment, caches, and session files.
- [ ] Provide a documented configuration template with placeholder values only.
- [ ] Add clear install/start/stop/upgrade instructions.
- [ ] Document database backup and restore.
- [ ] Test install and startup on a separate clean machine.
- [ ] Verify customer package can initialize a new database without relying on the developer's local DB.
- [ ] Decide delivery format (source package vs. installer) after clean-machine testing.
- [ ] Create and verify an immutable `v3.4.0` tag/release only after release approval.

## Product backlog
- [ ] Verify existing Telegram/NVD workflow end-to-end.
- [ ] Verify CRUD for all asset types and custom fields.
- [ ] Verify sidebar, table settings, pagination, and responsive layout.
- [ ] Confirm runtime data and secrets are excluded from Git.
