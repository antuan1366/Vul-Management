# PROJECT MAP

## Repository
GitHub: antuan1366/Vul-Management.

Local path depends on the checkout:
- Original checkout: E:\Vul-Management (port 8001; do not touch unless explicitly asked).
- User test copy: E:\Vul (port 8000).

## Backend
- Entry point: backend/app/main.py.
- API routes: backend/app/api/, including authentication, user and threat-intelligence routes.
- Core configuration: backend/app/core/config.py (application version); backend/app/core/database_version.py (schema compatibility).
- Models: backend/app/models/, including user, asset, feed and threat-intelligence models.
- Pydantic schemas: backend/app/schemas/.
- Business logic/integrations: backend/app/services/.
- Scan Result inventory matching: backend/app/services/asset_message_matching.py.
- Database/session setup: backend/app/database.py.
- Migrations: backend/alembic/versions/; latest known migration 0011, for Vulnerability Register custom fields.
- Tests: tests/; asset-match tests are in tests/test_asset_message_matching.py.

## Frontend
- Shared layout: frontend/src/layouts/main.html.
- Pages: frontend/src/pages/.
- Shared services: frontend/src/services/.
- Global styles: frontend/src/styles/main.css.
- Sidebar and version footer: frontend/src/services/sidebar.js.
- Table preferences: frontend/src/services/table-preferences.js.
- Threat-intelligence UI: frontend/src/pages/scan-result.html, frontend/src/pages/vulnerabilities.html and frontend/src/services/threat-intelligence.js.

## Known pages
- login.html, setup.html, change-password.html, users.html
- dashboard.html
- equipment.html, operating-systems.html, applications.html, libraries.html, asset-fields.html
- vulnerability-scan.html, scan-result.html, vulnerabilities.html
- vulnerability-feeds.html, telegram-feeds.html, telegram-settings.html
- Nessus-related views, Administration and logs-events.html; confirm exact files/routes in the current tree.

The route, filename and visible navigation label may differ. Inspect sidebar.js before changing navigation.

## Project documentation
- START_HERE.md: onboarding and read order.
- PROJECT.md: purpose, scope and workflow.
- STATE.md: current implementation, verification and known gaps.
- SESSION.md: immediate continuation and safety notes.
- ARCHITECTURE.md: boundaries and data/workflow design.
- UI_STYLE_GUIDE.md: visual/interaction contract.
- DECISIONS.md: durable architectural/product decisions.
- STRATEGY.md: development sequence.
- TODO.md: verification backlog.
- RULES.md: contributor constraints.
- COMPATIBILITY.md: application/database compatibility.
- V3.6.5_RELEASE.md: current promotion notes; other versioned records are historical.

## Runtime database
backend/data/vul_management.db

This is local runtime state. Never include it in Git or delete it as a routine troubleshooting step.

## Local development
Expected backend working directory: E:\Vul\backend for the test copy. Use the exact virtual-environment Python if shell activation is blocked. Verify branch, repository path, port and database path before commands that change state.

- Test-copy app: http://127.0.0.1:8000/
- API info: http://127.0.0.1:8000/api/info
- Swagger: http://127.0.0.1:8000/docs
