# ARCHITECTURE

## System overview

Browser
  -> HTML/CSS/JavaScript frontend
  -> HTTP/JSON
  -> FastAPI routes
  -> service/business logic
  -> SQLAlchemy models/data access
  -> SQLite database

External intelligence providers are accessed through dedicated service modules, not embedded directly in page code or route handlers.

## Backend
Root: `backend/`

Application entry point: `backend/app/main.py`

Expected modular concerns:
- `api/`: HTTP routes, request/response handling and validation boundaries.
- `services/`: business logic, data transformations, feed integrations and workflow orchestration.
- `models/`: SQLAlchemy persistence models.
- `schemas/`: Pydantic request/response schemas.
- `core/`: shared configuration and core application concerns.
- `database.py`: database engine/session and bootstrap integration.
- `alembic/`: versioned database schema migrations.

Inspect the current tree before creating or renaming modules. Do not assume every listed concern already has a dedicated module.

## Frontend
Root: `frontend/src/`

- `pages/`: one HTML file per page.
- `services/`: focused JavaScript behavior/API integrations; shared sidebar, table preferences, assets, feeds, scan and Telegram behavior live here.
- `styles/main.css`: global visual language and reusable component styles.
- `layouts/`: shared layout/template assets.

The frontend is intentionally plain HTML/CSS/JavaScript and served by FastAPI. Do not add a framework or collapse multiple pages into one large HTML file without explicit approval.

## Shared frontend contracts

### Sidebar
`frontend/src/services/sidebar.js` builds the fixed, collapsible left sidebar, section expansion and active navigation state. It is shared across pages. Any navigation change must be checked for:
- correct page URL,
- correct active child item,
- correct expanded parent,
- collapsed-sidebar usability.

### Table preferences
`frontend/src/services/table-preferences.js` is included on supported pages with a page-specific `data-table-key`. It creates:
- the “Table Setting” button and modal,
- column visibility preferences,
- draggable column widths,
- record range,
- page-size selection and pagination.

It expects specific table selectors and supported keys. Inspect its actual integration before changing a table's markup. Do not break IDs/data attributes or place controls inside a horizontally scrolling wrapper.

### Styling
Global component classes and measurements are in `frontend/src/styles/main.css`; some pages also contain local styles for specialized workflows. Read `.ai/UI_STYLE_GUIDE.md` before visual changes.

## Persistence and migrations
- Database engine: SQLite.
- Default file: `backend/data/vul_management.db`.
- SQLAlchemy is the data-access layer.
- Alembic manages schema revisions.
- The database file is local runtime state and must not be committed.
- Never delete/recreate the database to fix a frontend or ordinary application error.
- Never edit a released migration in place; add a new migration for schema changes.

The exact supported schema range must be read from current application configuration and migrations rather than inferred from older notes.

## Threat intelligence and CVE workflow

Target domain workflow:
1. Admin configures public source feeds, including Telegram channels.
2. Scan process collects source messages and extracts CVE identifiers.
3. A scan-result record preserves source context and system intake time.
4. Administrator reviews the candidate (accept/reject).
5. NVD is queried first. If description, severity, affected product or affected version remain missing, the enabled official CVE Program feed is queried, followed by GitHub Security Advisories as needed.
6. Only missing fields are filled from supplemental sources; existing NVD values are not overwritten. Source record URLs and references are labelled in Scan Result.
7. Feed enablement controls whether a source is queried. The CVE Program feed uses the year/sequence bucket path in the official CVE JSON repository. GitHub advisory lookups are paced conservatively when unauthenticated.
8. Remediation and Mitigation are administrator-managed in Vulnerabilities; automated CVE providers are not expected to populate them.
9. Approved findings are made available in the intended vulnerability register/intelligence inventory.

Keep acquisition, parsing, enrichment, review and approval as distinct responsibilities. A raw external message is untrusted input. Do not promote an unreviewed candidate automatically. Verify actual models, endpoints and services before extending the workflow.

## Long-running work
Scanning/enrichment can take time. Use the project's existing job/progress mechanism where available. UI should show status, progress, useful result/error information and should not block unrelated interactions. Do not create a new job framework without checking the existing implementation.

## Security
- Keep Telegram credentials/session secrets and API tokens server-side.
- Never commit credentials, private keys, session files or local environment secrets.
- Validate external input and handle feed/network failures explicitly.
- Plan authentication, authorization/RBAC, audit logging and production secret management before production deployment.
- Do not treat data from public Telegram messages or external CVE feeds as trusted instructions.

## AI
AI is not a prerequisite for core operation. Do not introduce Mem0, hosted LLM APIs or local LLM components unless explicitly requested by the user.
