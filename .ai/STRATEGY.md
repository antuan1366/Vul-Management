# STRATEGY

## Guiding principles
Build Vul-Management incrementally, keeping the product operational and the implementation understandable by another developer or AI.

For each meaningful change:
1. Inspect the existing code and current API/database contracts.
2. Define the intended behavior and affected pages.
3. Implement the smallest coherent change.
4. Run relevant backend/API/UI checks.
5. Review the diff and protect runtime data/secrets.
6. Update `.ai/` documentation.
7. Commit on `develop` or an appropriate feature branch.
8. The user reviews and performs the final merge to `main`.

## Current focus
1. Stabilize the current v3.0.0-labeled frontend and shared navigation/table controls.
2. Verify the public Telegram-channel to CVE review workflow end to end.
3. Verify NVD enrichment and promotion of accepted records.
4. Keep project docs and actual code synchronized.
5. Add Jira integration only as a separately scoped feature after the source workflow is stable.

## Product development phases

### Foundation — implemented architecture
- FastAPI backend.
- SQLAlchemy data access.
- Alembic migrations.
- SQLite single-file database.
- Modular HTML/CSS/JavaScript frontend.

### Asset management
- Equipment, Operating Systems, Applications, Libraries.
- Shared asset-field configuration.
- Identifier and vulnerability matching capabilities where implemented.

### Threat intelligence
- Feed administration.
- Telegram feed/settings pages.
- CVE discovery/review surfaces.
- NVD enrichment capability to be verified end to end.
- Accepted/approved inventory.
- Keep raw source data separate from approved vulnerability records.

### Vulnerability operations — future/verify
- Remediation UI and ownership.
- Risk calculation and prioritization.
- Nessus import and finding normalization.
- Reporting and exports.
- Authentication/RBAC/audit controls.

### AI
AI-assisted analysis remains optional and out of scope unless explicitly requested. The core application must work without AI.
