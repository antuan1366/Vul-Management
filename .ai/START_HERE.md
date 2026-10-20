# START HERE

## Project
Vul-Management — version **3.6.5** (selected version for the current release promotion).

- Repository: antuan1366/Vul-Management.
- Development branch: develop.
- Release integration target: main; this promotion was explicitly authorized by the user and must be performed/confirmed through a pull request.
- Stack: FastAPI, SQLAlchemy, Alembic, SQLite, plain HTML/CSS/JavaScript.
- Latest schema migration: 0011; schema declarations remain 1–11.

## Read order
1. PROJECT.md
2. STATE.md
3. SESSION.md
4. STRATEGY.md
5. ARCHITECTURE.md
6. PROJECT_MAP.md
7. UI_STYLE_GUIDE.md
8. DECISIONS.md
9. TODO.md
10. RULES.md
11. COMPATIBILITY.md
12. V3.6.5_RELEASE.md
13. Historical records such as V3.2.0_RELEASE.md and V3.1.0_NESSUS.md.

Inspect actual source files relevant to the task. If docs and code disagree, verify behavior and then correct the docs.

## Current feature areas
- Asset inventory and administrator-managed asset fields.
- Telegram scan, CVE extraction/review and NVD-first multi-source enrichment.
- Vulnerability Register custom fields, combined product/version display and Scan Result asset-match hints.
- Nessus manual scan, finding review and host mapping.
- Local login, user administration, authentication middleware and Logs & Events.
- Jira issue-creation service exists in source but needs end-to-end verification.

## Verification
Previous user-reported page smoke tests are historical evidence only and do not certify release 3.6.5. See V3.6.5_RELEASE.md and TODO.md for current unverified test areas.

## Database and secret safety
- Default SQLite path: backend/data/vul_management.db.
- Never delete, reset, recreate or overwrite backend/data/ to solve a code issue without explicit approval and a verified backup.
- Never commit database files, credentials, tokens, Telegram session files or private keys.
- Use Alembic for schema changes and verify the selected database path before migrations.

## Local path distinction
- The historical/original checkout E:\Vul-Management runs on port 8001 and must not be changed unless explicitly requested.
- The user's test copy E:\Vul runs on port 8000.
- Confirm the branch, path and port before commands that change files or runtime state.

## Git workflow
- Develop on develop or a focused feature branch.
- Inspect branch and working tree status before risky operations.
- Do not force-push, reset local history, run git clean, discard work or merge to main without explicit user authorization.
- For this 3.6.5 promotion, the user has explicitly authorized the merge; use a pull request and verify the final merged state.
- Create a tag/release only after appropriate verification and explicit release approval.

## Authentication note
When no users exist, current source creates local/testing default admin / vulmgm without forcing a first-login password change. Change the shared default before exposing the app to an untrusted network.
