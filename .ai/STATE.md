# STATE

## Snapshot
- Project: Vul-Management
- Version declaration: 3.6.0 (Scan Result asset-message matching and attention flags)
- Active development branch: `develop`
- Declared schema range: 1–11
- Latest known migration: 0011
- Backend and sidebar version declarations are 3.6.0.
- Local login and user administration are implemented on develop: automatic first-admin bootstrap when no users exist, sign-in/sign-out, signed HTTP-only session cookie, PBKDF2 password hashes, account enable/disable, Admin/User roles, password reset, and last-active-admin safeguards.
- Authenticated access is enforced server-side for app HTML pages, data APIs, and API documentation. Login attempts are throttled in-process after 10 failed attempts within five minutes.
- Vulnerability Register custom fields are stored per record in `threat_intelligence.custom_fields_json`; definitions are admin-managed in `vulnerability_custom_fields` and added by migration 0011. Field names can be edited, fields can be required, and table visibility is configurable. Vulnerability Register and Scan Result display affected product and version in one column each.
- Vulnerability Register and Scan Result tables now omit their Severity column while retaining CVSS/Score. Scan Result Details and status controls share aligned control styling. Table preferences use stable keys for these two changed layouts and migrate prior index-based column/width preferences without shifting settings onto the wrong columns.
- Scan Result now calculates advisory asset matches against current Equipment, Operating System, Application and Library inventory records. It checks identifying fields such as names, vendors/brands, models, IP/serial identifiers, CPE/PURL/package identifiers and non-generic custom asset-field values. Matching rows receive a highlight and an Asset Match flag; Details shows the matched asset and terms. This is a heuristic hint, not proof that an asset is affected; match computation is dynamic and does not require a schema migration.
- Migration 0009 adds the users table; migration 0010 adds `must_change_password`. If no users exist at startup, a default `admin` account is created with password `vulmgm` and does not require a forced password change. A previous bootstrap account is converted to the configured default only if it is still marked as requiring its first password change; established passwords are preserved. When VULM_SESSION_SECRET is not set, a signing key is generated under the ignored local data directory.
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
1. Back up a test database, upgrade it through migrations 0009–0011, and verify existing asset and intelligence records remain intact.
2. Confirm the first-run `admin` account is created with the configured default password only when the users table is empty.
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
