# START HERE

## Project
Vul-Management

## Repository and branch
- Repository: `antuan1366/Vul-Management`
- Active development branch: `develop`
- Do not merge to `main` unless the user explicitly approves it.
- User prefers direct, practical steps and complete replacement files when code edits are requested.

## Purpose
A modular vulnerability-management platform for asset inventory, vulnerability discovery and review, threat intelligence, remediation tracking and future reporting/integrations.

## Current UI version label
The shared sidebar currently displays **v3.0.0**. Treat the running source and actual API behavior as authoritative; do not infer that every planned feature is implemented just from a version label.

## Current application shape
- Backend: Python, FastAPI, SQLAlchemy, Pydantic, Alembic, SQLite.
- Frontend: plain HTML, CSS and JavaScript served by FastAPI.
- Database: `backend/data/vul_management.db`; local runtime data, intentionally not tracked by Git.
- Main frontend folders: `frontend/src/pages/`, `frontend/src/services/`, `frontend/src/layouts/`, `frontend/src/styles/`.
- The sidebar and shared table preferences are reusable services, not page-specific copies.

## Read order for any AI
1. `PROJECT.md`
2. `STATE.md`
3. `SESSION.md`
4. `STRATEGY.md`
5. `ARCHITECTURE.md`
6. `PROJECT_MAP.md`
7. `UI_STYLE_GUIDE.md`
8. `DECISIONS.md`
9. `TODO.md`
10. `RULES.md`
11. `COMPATIBILITY.md`

Then inspect the actual source files relevant to the requested change. If documentation and code disagree, report the discrepancy and verify behavior instead of assuming either one is correct.

## Current implemented areas to verify in source
- Asset pages: Equipment, Operating Systems, Applications, Libraries.
- Dynamic asset field configuration.
- Threat Intelligence navigation with Vulnerability Scan, Scan Result and Vulnerability Register routes in current source.
- Telegram feed administration and Telegram account settings/verification UI.
- Scan results with CVE review actions and NVD enrichment UI.
- Vulnerability register/management pages and vulnerability feed configuration.
- Shared dark collapsible sidebar and light content workspace.
- Table Setting dialog, column visibility/width preferences and pagination on integrated tables.

## Important product workflow
Public Telegram channels are intended to be scanned for CVEs. Scan results should retain the original message context, be reviewed by an administrator, and be enriched from NVD before approved items are promoted into the vulnerability intelligence/register workflow. Verify the backend implementation before changing this flow. Jira issue creation is a planned product capability, not to be assumed implemented.

## Database safety
- SQLite is the current database.
- Never delete, reset, recreate or replace `backend/data/` to solve a code or migration issue without explicit user approval and a verified backup.
- Use SQLAlchemy for application data access and Alembic for schema changes.
- Never commit runtime database files, credentials, tokens or private keys.

## Git workflow
- Work on `develop` or a feature branch.
- Inspect `git status` before destructive Git operations.
- Do not use `git clean`, force-push, reset local history or merge into `main` unless the user explicitly requests that exact action.
- After local verification, update these project notes and clearly report what was and was not tested.

## Current priority
Keep the existing working application stable, make UI changes consistent with `UI_STYLE_GUIDE.md`, verify Telegram-to-CVE review flow against actual code, and keep the project documentation aligned with the implementation.
