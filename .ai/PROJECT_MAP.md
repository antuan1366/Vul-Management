# PROJECT MAP

## Repository
`E:\Vul-Management`

## Backend
- App entry: `backend/app/main.py`
- API routes: `backend/app/api/`
- Core/configuration: `backend/app/core/`
- SQLAlchemy models: `backend/app/models/`
- Pydantic schemas: `backend/app/schemas/`
- Business logic/integrations: `backend/app/services/`
- Database setup: `backend/app/database.py`
- Migrations: `backend/alembic/versions/`

Inspect the live repository tree before assuming exact module filenames.

## Frontend
- Shared layout: `frontend/src/layouts/main.html`
- Pages: `frontend/src/pages/`
- Shared services: `frontend/src/services/`
- Global styles: `frontend/src/styles/main.css`
- Sidebar: `frontend/src/services/sidebar.js`
- Table preferences: `frontend/src/services/table-preferences.js`

## Known frontend pages
- `dashboard.html`
- `equipment.html`
- `operating-systems.html`
- `applications.html`
- `libraries.html`
- `asset-fields.html`
- `vulnerability-scan.html`
- `scan-result.html`
- `vulnerabilities.html`
- `vulnerability-feeds.html`
- `telegram-feeds.html`
- `telegram-settings.html`
- `logs-events.html`

The route/page name and displayed navigation label may differ. Inspect `sidebar.js` before changing either.

## Project documentation
- `.ai/START_HERE.md`: onboarding and reading order.
- `.ai/PROJECT.md`: project scope and intended workflows.
- `.ai/STATE.md`: current known state and discrepancies.
- `.ai/SESSION.md`: latest work and immediate continuation.
- `.ai/ARCHITECTURE.md`: system boundaries.
- `.ai/UI_STYLE_GUIDE.md`: visual and interaction contract for humans/AI.
- `.ai/DECISIONS.md`: durable decisions.
- `.ai/STRATEGY.md`: development sequence.
- `.ai/TODO.md`: current backlog and verification.
- `.ai/RULES.md`: constraints for AI contributors.
- `.ai/COMPATIBILITY.md`: app/database compatibility policy.

## Runtime database
`backend/data/vul_management.db`

This is local runtime data. Never include it in Git or delete it as a routine troubleshooting step.

## Local development
Expected backend working directory: `E:\Vul-Management\backend`

Expected command:
`python -m uvicorn app.main:app --reload`

Use the project's virtual environment Python if PowerShell activation is blocked. Verify the actual environment/dependencies before troubleshooting import errors.

## Useful local URLs
- App: `http://127.0.0.1:8000/`
- API info: `http://127.0.0.1:8000/api/info`
- Swagger: `http://127.0.0.1:8000/docs`
