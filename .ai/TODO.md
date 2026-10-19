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

## Customer deployment
- [ ] Define supported OS and Python version.
- [ ] Create a clean package excluding local database, credentials, virtual environment, caches, and session files.
- [ ] Provide a documented configuration template with placeholder values only.
- [ ] Add clear install/start/stop/upgrade instructions.
- [ ] Document database backup and restore.
- [ ] Test install and startup on a separate clean machine.
- [ ] Verify customer package can initialize a new database without relying on the developer's local DB.
- [ ] Decide delivery format (source package vs. installer) after clean-machine testing.
- [ ] Create and verify an immutable `v3.2.0` tag/release only after release approval.

## Product backlog
- [ ] Verify existing Telegram/NVD workflow end-to-end.
- [ ] Verify CRUD for all asset types and custom fields.
- [ ] Verify sidebar, table settings, pagination, and responsive layout.
- [ ] Confirm runtime data and secrets are excluded from Git.
