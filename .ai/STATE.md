# STATE

## Current snapshot
- Project: Vul-Management.
- User-selected version for this promotion: **3.6.5**.
- Active development branch: develop; main receives approved releases through a pull request.
- Application schema declaration: minimum 1, maximum 11.
- Latest migration: 0011_vulnerability_custom_fields.py; this release does not add a migration.
- Runtime database default: backend/data/vul_management.db.
- Backend API version and sidebar version are set to 3.6.5.
- This is the user-selected version label for the current accumulated develop changes. Do not imply separate 3.6.1–3.6.4 releases were published.

## Implemented in current source
- Asset inventory: Equipment, Operating Systems, Applications and Libraries, including administrator-managed asset fields.
- Nessus manual scan, finding views and host-mapping workflow are present in source; upload, parsing and promotion still need end-to-end verification.
- Telegram source configuration and scan workflow extract CVEs while retaining source-message context and use administrator review before promotion.
- CVE enrichment tries NVD first and can use enabled supplemental CVE Program and GitHub Security Advisory sources when key fields remain incomplete. Source references are labelled; provider calls honor feed enablement and pacing.
- Vulnerability Register custom fields are administrator-managed. Values are stored in threat_intelligence.custom_fields_json; definitions use migration 0011. Affected Product and Affected Version are combined for table presentation while underlying values remain distinct.
- Vulnerability Register and Scan Result show CVSS/Score without a separate Severity table column. Table preferences use stable keys for the changed layouts.
- Scan Result computes advisory matches against live Equipment, Operating System, Application and Library inventory, including identifying fields and useful custom field values. Rows are highlighted and flagged; details list matched assets and terms. This is heuristic evidence, not proof an asset is vulnerable, and it does not require a migration.
- Local accounts use signed HTTP-only session cookies and PBKDF2-HMAC-SHA256 password hashes. Server-side authentication protects application pages, APIs and API documentation. Admin can manage local users; finer authorization for non-user-management operations still needs review.
- When the users table is empty, current source bootstraps the local/testing account admin / vulmgm; first login is not forced to change this default. Change it before exposing the app to an untrusted network. Established passwords are preserved.
- A session-signing key is generated in the ignored local data directory when VULM_SESSION_SECRET is not configured.
- A Jira issue-creation service exists in source, but the integration is not considered verified until tested against a non-production Jira project.

## Verification status
- The user previously reported page-level smoke checks for Asset Management, Nessus Manual Scan, Nessus Scan Results, Threat Intelligence, Administration and Logs & Events. Those checks are not full end-to-end validation of version 3.6.5.
- Automated asset-message matching tests exist in tests/test_asset_message_matching.py, but they have not been executed in this working session.
- Do not claim 3.6.5 runtime, migration, browser, Nessus, Telegram, enrichment or Jira tests passed unless their results are recorded explicitly.

## Release 3.6.5 verification checklist
1. Run python -m unittest discover -s tests -p test_asset_message_matching.py from the repository root.
2. Back up a test database; inspect Alembic current/history and confirm migration 0011 compatibility. Do not run migrations against the user's live database without an explicit plan and verified backup.
3. Check /api/info reports application version 3.6.5 and schema values consistent with configuration and the selected database.
4. Verify login/logout, session expiry, inactive-user rejection, API/docs protection and Admin/User access boundaries.
5. Test Vulnerability Register custom-field CRUD, required validation, values on edit and dynamic columns.
6. Test representative asset matching, custom fields, IPv4 addresses, word boundaries, false positives and refreshed inventory values.
7. Run sanitized end-to-end Nessus and Telegram workflows; validate review, enrichment, promotion and deduplication.
8. Validate Jira using a non-production project and token; never put credentials in Git or logs.
9. Test clean installation/upgrade and backup/restore on a separate machine before treating the package as production-ready.

## Safety
- Preserve local runtime databases, session-signing keys, Telegram session files and credentials.
- Never commit database files, tokens, passwords, private keys, virtual environments or cache files.
- Do not force-push, reset or discard local work as routine troubleshooting.
