# STATE

## Snapshot
- Project: Vul-Management
- Version declaration: 3.2.0
- Active development branch: `develop`
- Declared schema range: 1–8
- Latest known migration: 0008
- Backend and sidebar version declarations were updated to 3.2.0.
- Multi-source CVE lookup code is committed on `develop`: NVD first, then the official CVE Program record and GitHub Security Advisories when description/severity/product/version fields remain missing.
- Two new built-in feed types are seeded at application startup: `cve_program` and `github_advisory`. Feed enablement is respected.
- Supplemental provider references are labelled in Scan Result details. Remediation and Mitigation remain administrator-managed in Vulnerabilities and are not part of automated source completeness.
- GitHub unauthenticated advisory lookups are deliberately paced at 65 seconds per request; configuring a GitHub token in the feed enables a higher quota. NVD requests retain the conservative 8-second limiter.
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
1. Test feed seeding on restart and use each Feed `Test` action for NVD, CVE Program and GitHub Security Advisories.
2. Use Scan Result → Details → `Refresh Sources` on an already-stored partial/not-found CVE and verify data, status and labelled references refresh correctly.
3. Run an end-to-end Telegram scan containing `CVE-2018-10388`; verify the CVE Program description and labelled references appear even if severity/product/version remain unavailable.
4. Verify NVD-not-found and transient HTTP failures do not prevent the two supplemental feeds from being queried.
5. Verify disabled feeds are not called, and verify incomplete/no-result CVEs can be retried on a later scan.
6. Validate Alembic migration and schema compatibility against a backed-up test DB (this feature adds no database columns).
7. Create a deployment package that excludes local database, secrets, virtual environment, and cache files.
8. Install and test the package on a separate clean Windows machine.
9. Create a version tag/release only after final release verification and approval.

## Safety
Do not delete or replace local runtime data. Do not claim tests passed unless the user or an automated test actually confirmed them.
