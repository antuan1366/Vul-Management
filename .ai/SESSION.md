# SESSION

## Current state
- Current version declaration: 3.5.0 on develop; database schema target is 11 (migration 0011).
- Current feature work is on `develop`; do not merge to `main` without explicit approval.
- The user reports successful local startup and successful page-level smoke checks for Asset Management, Nessus Manual Scan, Nessus Scan Results, Threat Intelligence, Administration, and Logs & Events.

## Authentication and user administration (new; runtime unverified)
- If no users exist, startup creates the local/testing default `admin` / `vulmgm`. Established account passwords are preserved. Change this shared default before exposing the application to an untrusted network.
- Login sessions use signed HTTP-only cookies with an eight-hour maximum age; passwords use PBKDF2-HMAC-SHA256.
- Admin-only account management supports create/edit/password reset/disable/delete and protects the last active administrator.
- App pages, data APIs, and docs are gated by server-side authentication middleware.
- Verify migration 0009, session behavior, direct API protection and role handling locally before considering this feature validated.

## Vulnerability Register custom fields (new; runtime unverified)
- Migration 0011 adds a JSON custom-value column to Vulnerability Register records and a table for custom field definitions.
- Admin can create/rename/delete custom text fields, mark them required, and choose whether they appear as table columns. Field values persist per CVE.
- Affected Product and Affected Version are combined into one column in both Vulnerability Register and Scan Result. Table preference migration was updated for the changed columns.
- Verify migration 0011 on a backed-up existing database; test custom field CRUD, validation, values on create/edit, dynamic columns, and Admin-only write permissions.

## Nessus workflow in source
- Manual Scan page supports Nessus file upload and a separate analysis action.
- The backend declares parsing dependencies including `defusedxml` and `python-multipart`.
- Findings review and host mapping are present in the current source.
- Do not treat page visibility as proof that file upload, XML parsing, finding acceptance, deduplication, or mapping has passed end-to-end testing.

## Next verification
1. Check `/api/info` reports version 3.2.0 and the expected schema version.
2. Check Alembic current/history and migration behavior against a backed-up test database before any customer migration.
3. Upload and analyse a synthetic Nessus XML fixture; verify expected host and finding counts.
4. Test New, Under Review, Accept, and Reject actions.
5. Confirm accepted CVE findings appear once in the shared vulnerability register and findings without CVEs cannot be promoted.
6. Test hostname/FQDN/IP/MAC/UUID host mapping.
7. Exercise Telegram scan, review, NVD enrichment, and promotion with controlled test data.
8. Verify Jira integration with a test project before enabling it for a customer.
9. Prepare and test a clean deployment package on a separate machine.

## Safety
- Preserve the local runtime database.
- Do not change `.ai/` on the user's working copy until the documentation PR is reviewed/merged and pulled.
- Do not claim unperformed API, migration, integration, or clean-machine tests.
