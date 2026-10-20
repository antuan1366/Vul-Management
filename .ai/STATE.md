# STATE

## Snapshot
- Project: Vul-Management
- Version declaration: 3.4.0 (automatic first-admin bootstrap and forced password change added on develop)
- Active development branch: `develop`
- Declared schema range: 1–10
- Latest known migration: 0010
- Backend and sidebar version declarations are 3.4.0.
- Local login and user administration are implemented on develop: automatic first-admin bootstrap when no users exist, forced initial password change, sign-in/sign-out, signed HTTP-only session cookie, PBKDF2 password hashes, account enable/disable, Admin/User roles, password reset, and last-active-admin safeguards.
- Authenticated access is enforced server-side for app HTML pages, data APIs, and API documentation. Login attempts are throttled in-process after 10 failed attempts within five minutes.
- Migration 0009 adds the users table; migration 0010 adds `must_change_password`. If no users exist at startup, a default `admin` account is created with a cryptographically random temporary password stored in the ignored local file `backend/data/INITIAL_ADMIN_CREDENTIALS.txt`; the first login forces password change and then deletes that credential file. Existing accounts are not overwritten. When VULM_SESSION_SECRET is not set, a signing key is generated under the ignored local data directory.
- Multi-source CVE lookup code is committed on `develop`: NVD first, then the official CVE Program record and GitHub Security Advisories when description/severity/product/version fields remain missing.
- Two new built-in feed types are seeded at application startup: `cve_program` and `github_advisory`. Feed enablement is respected.
- Supplemental provider references are labelled in Scan Result details. Remediation and Mitigation remain administrator-managed in Vulnerabilities and are not part of automated source completeness.
- Rate pacing was modestly increased on `develop`: NVD is 7 seconds without a key and 2.5 seconds with an API key; GitHub Advisories are 62 seconds unauthenticated and 1 second authenticated. These are local per-process limiters, not shared limits across multiple app instances or other clients sharing the same IP/account.
- The Scan Result details modal has a `Refresh Sources` action that calls the multi-source enrichment endpoint for an existing non-rejected result.
- Previously partial and not-found CVEs are eligible for a later scan retry; only a complete `success` row is cached. Placeholder values such as `n/a` and `Version range not specified` no longer block source fallback.
- Disabling the NVD CVE feed disables NVD lookup rather than silently calling its hard-coded public endpoint.

## User-reported verification
Local app startup succeeded. The user reports page-level smoke tests passed for:
- Asset Management
- Nessus Manual Scan
- Nessus Scan Results
- Threat Intelligence
- Administration
- Logs & Events

This confirms basic navigation/page rendering only. The following remain unverified unless separately tested: database migration on a clean database, Nessus upload and parsing, finding review transitions, register deduplication, host mapping, Telegram scan/enrichment, Jira issue creation, and deployment on a clean machine.

## Existing platform
- FastAPI, SQLAlchemy, Alembic, SQLite, plain HTML/CSS/JavaScript.
- Asset inventory for Equipment, Operating Systems, Applications, and Libraries.
- Telegram-based threat-intelligence workflow and shared vulnerability register.
- Nessus import/finding tables and host-mapping workflow in source.
- Runtime database default: `backend/data/vul_management.db`.

## Next steps
1. Back up a test database, upgrade it through migrations 0009–0010, and verify existing asset and intelligence records remain intact.
2. Confirm the first-run `admin` account and local temporary credential file are created only when the users table is empty.
3. Verify first login is forced to the change-password page; after change, access is restored and the temporary credential file is deleted.
2. Test first-admin setup, sign-in/sign-out, eight-hour session expiry, disabled-user rejection, and protected page/API/docs routes.
5. Test user creation, duplicate usernames, role changes, password reset, disabling/deleting users, and protection against locking out the last active administrator.
6. Test feed seeding on restart and use each Feed Test action for NVD, CVE Program and GitHub Security Advisories.
7. Use Scan Result → Details → Refresh Sources on an already-stored partial/not-found CVE and verify data, status and labelled references refresh correctly.
8. Run an end-to-end Telegram scan containing CVE-2018-10388 and verify the CVE Program description/source reference appears when available.
9. Verify disabled feeds are not called, incomplete CVEs can be retried, and transient HTTP failures do not prevent fallback sources from being queried.
10. Test Jira issue creation using a non-production project and API token.
11. Run automated/backend checks and record exact results.
12. Create a deployment package that excludes local database, secrets, virtual environment and cache files.
13. Install and test the package on a separate clean Windows machine.
14. Create a version tag/release only after final release verification and approval.

## Safety
Do not delete or replace local runtime data. Do not claim tests passed unless the user or an automated test actually confirmed them.
