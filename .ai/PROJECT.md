# PROJECT

## Identity
- Name: Vul-Management
- Repository: `antuan1366/Vul-Management`
- Active development branch: `develop`
- Current backend/sidebar version declaration in source: 3.5.0 (development)

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
8. User Management and login/session handling
9. Future reporting, remediation, risk prioritization and integrations

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
6. Enrich CVEs from NVD first, then enabled supplemental feeds such as the official CVE Program and GitHub Security Advisories when important fields are missing. Preserve source provenance in labelled references.
7. Have an administrator define Remediation, Mitigation, and any deployment-specific custom fields in Vulnerabilities; custom field definitions and table visibility are administrator-managed. These fields are not required from external CVE APIs.
8. Promote approved items into the vulnerability intelligence/register workflow.
9. Jira issue creation is a desired integration and must be treated as incomplete until implemented and tested.

Do not mark each step as implemented based only on this description. Inspect backend routes, models, services and frontend handlers.

## Authentication and account administration
- If the users table is empty, startup creates the default `admin` account with password `vulmgm`; first login is not forced to change it. A previous bootstrap account is converted to the requested default only if it is still marked as requiring its first password change. Established passwords are preserved. The shared default is for local/testing only and must be changed before exposing the app to an untrusted network.
- Administrators can create, edit, disable, reset passwords for and delete accounts; the last active administrator cannot be locked out through normal UI/API operations.
- Sessions use signed, HTTP-only cookies; password hashes use PBKDF2-HMAC-SHA256.
- The Admin role manages accounts. The User role cannot access user-management endpoints; finer permissions for other application actions remain future work and must be reviewed before production exposure.

## Database
- Engine: SQLite.
- Schema target on `develop`: 11 (migration 0011 adds custom fields to the Vulnerability Register).
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
