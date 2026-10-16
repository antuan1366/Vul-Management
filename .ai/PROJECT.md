# PROJECT

## Identity
- Name: Vul-Management
- Repository: `antuan1366/Vul-Management`
- Active development branch: `develop`
- Current UI version label in source: `v3.0.0`

## Goal
Build a modular web application for vulnerability management and threat intelligence, with an asset inventory, vulnerability discovery, human review, NVD enrichment, remediation workflow and reporting. The application should remain understandable and maintainable by another developer or AI using the documentation in `.ai/`.

## Technology
### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- SQLite

### Frontend
- HTML
- CSS
- Plain JavaScript
- Served by FastAPI; no frontend framework is required by the current architecture.

## Main areas
1. Dashboard
2. Assets: Equipment, Operating Systems, Applications, Libraries
3. Dynamic asset-field configuration
4. Threat Intelligence: Vulnerability Scan, Scan Result, Vulnerability Register (current source labels/routes; intended user-facing register label is **Vulnerabilities**, so verify and reconcile the sidebar text)
5. Vulnerability feeds
6. Telegram feeds and Telegram account/session configuration
7. Logs & Events
8. Future reporting, remediation, risk prioritization and integrations

## Asset management
- The administrator enters known asset information.
- Asset categories have their own pages and field configuration.
- Shared asset-field behavior should be reused rather than copied across pages.
- Identifier/CPE/PURL logic and vulnerability applicability must be verified in the backend before being changed.
- Keep system fields and administrator-managed custom fields distinct.

## Threat-intelligence workflow
Target workflow:
1. Configure public Telegram channels/feeds in Administration.
2. Scan configured sources on a schedule or from a selected start date, where supported by the current implementation.
3. Extract CVE identifiers and preserve the source message/context.
4. Store scan results with a system intake timestamp and a concise table summary; expose full content on hover or in a detail view.
5. Allow an administrator to accept/reject or otherwise review findings.
6. Enrich accepted CVEs using NVD data such as severity, affected product/version and remediation/mitigation guidance where available.
7. Promote approved items into the vulnerability intelligence/register workflow.
8. Jira issue creation is a desired integration and must be treated as incomplete until implemented and tested.

Do not mark each step as implemented based only on this description. Inspect backend routes, models, services and frontend handlers.

## Database
- Engine: SQLite.
- Default path: `backend/data/vul_management.db`.
- SQLAlchemy is the data access layer.
- Alembic manages schema revisions.
- Database and other local runtime state are excluded from Git. Never delete or overwrite them casually.

## UI contract
The shared UI is a dark charcoal collapsible sidebar with a light workspace, white cards, neutral borders, compact operational tables, consistent primary/secondary/danger buttons, and modal-based forms where appropriate. The detailed rules and measurements are in `.ai/UI_STYLE_GUIDE.md`.

## AI development contract
An AI must:
- Read the `.ai/` documents before making changes.
- Inspect real source code and API contracts.
- Preserve modular files and existing working behavior.
- Avoid adding frameworks or dependencies without a clear need.
- Run relevant tests and report exact verification.
- Keep documentation current after significant changes.
