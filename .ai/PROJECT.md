# PROJECT

## Identity
- Name: Vul-Management.
- Repository: antuan1366/Vul-Management.
- Version selected for the current promotion: **3.6.5**.
- Ongoing development branch: develop; released/integrated changes are promoted to main through an explicitly authorized pull request.
- Database schema target: 11 (latest migration 0011).

## Goal
Build a modular web application for vulnerability management and threat intelligence, including asset inventory, vulnerability discovery, human review, enrichment, remediation workflow and reporting. Keep the application understandable to another developer or AI through the documentation in .ai/.

## Technology
### Backend
Python, FastAPI, SQLAlchemy, Pydantic, Alembic and SQLite.

### Frontend
Plain HTML, CSS and JavaScript served by FastAPI. Do not add a frontend framework without a clear need and explicit approval.

## Main areas
1. Dashboard.
2. Asset inventory: Equipment, Operating Systems, Applications and Libraries.
3. Administrator-managed asset fields.
4. Threat Intelligence: Scan, Scan Result and Vulnerability Register (user-facing label should be Vulnerabilities where appropriate).
5. NVD, official CVE Program and GitHub Security Advisory enrichment feeds.
6. Telegram feed administration, scan schedules and source-message review.
7. Nessus manual import, finding review and host mapping.
8. Local authentication, user management and Logs & Events.
9. Jira issue creation and future reporting/remediation workflow (Jira still requires end-to-end verification).

## Asset management
- Known assets are entered and maintained by the administrator.
- Asset categories have separate pages and field configuration.
- Reuse shared asset-field behavior rather than duplicating it.
- Keep system fields distinct from administrator-managed custom fields.
- Verify identifier/CPE/PURL logic and version applicability in the backend before changing it.

## Threat-intelligence workflow
1. Configure public Telegram channels/feeds in Administration.
2. Scan configured sources on a schedule or from a selected starting date, as implemented.
3. Extract CVE identifiers while preserving source context and the system intake timestamp.
4. Show concise summaries in Scan Result and retain full source text for details/hover.
5. Let an administrator review and accept/reject findings.
6. Query enabled sources: NVD first, then the official CVE Program and GitHub Security Advisories when key fields remain missing. Preserve provenance and respect per-source enablement/pacing.
7. Maintain Remediation, Mitigation and deployment-specific custom fields through administrator workflow where appropriate.
8. Promote approved findings into the shared vulnerability register.
9. Create Jira issues only after configuration is validated; verify against a non-production Jira project.
10. Compare original Scan Result messages with live asset identifiers/custom field values to flag possible matches. A match is advisory and is not a vulnerability applicability verdict.

Do not claim every step is end-to-end verified merely because the code path or UI exists.

## Authentication and account administration
- When no users exist, startup creates local/testing default account admin with password vulmgm; there is no forced first-login password change in the current bootstrap path. Change this default before exposing the app to an untrusted network.
- Passwords are stored using PBKDF2-HMAC-SHA256; session cookies are signed and HTTP-only.
- Admin can manage local user accounts; User is restricted from user-management operations. Fine-grained authorization for other application actions remains a production review item.

## Database
- Engine: SQLite; default path backend/data/vul_management.db.
- SQLAlchemy is the data-access layer; Alembic manages schema changes.
- Schema max on the current version: 11; migration 0011 provides Vulnerability Register custom-field storage.
- The database and local runtime state are excluded from Git. Never delete or overwrite them casually.

## UI contract
Use a dark charcoal collapsible sidebar and light workspace, white cards, neutral borders, compact operational tables, consistent action buttons and modal forms. See .ai/UI_STYLE_GUIDE.md.

## AI development contract
An AI contributor must read the .ai/ documents, inspect actual routes/models/services, preserve modular boundaries, run relevant tests, update this documentation after significant changes and clearly report unverified areas. Core operation must not depend on AI.
