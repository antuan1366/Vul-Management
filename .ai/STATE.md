# STATE

## Snapshot
- Project: Vul-Management
- Active branch: `develop`
- Current version text shown in shared sidebar: `v3.0.0`
- Last known GitHub change before this documentation update: `a5c69d6 Replace table settings gear with Table Setting label`
- This document describes the known code/UI state, not a guarantee that all workflows have been runtime-tested.

## Confirmed from current source
- FastAPI-hosted frontend using plain HTML/CSS/JavaScript.
- Dark collapsible sidebar and light content workspace.
- Sidebar groups: Dashboard, Assets, Threat Intelligence, Reporting, Administration.
- Asset pages: Equipment, Operating Systems, Applications, Libraries.
- Asset field configuration page.
- Vulnerability Scan, Scan Result, Vulnerability Register pages.
- Vulnerability feed management.
- Telegram Feeds and Telegram Settings pages, including account verification flow in the UI.
- Logs & Events page.
- Shared Table Setting control in `frontend/src/services/table-preferences.js`; it supports column visibility, column resizing, page size and pagination for integrated tables.
- SQLite database path: `backend/data/vul_management.db`.
- SQLAlchemy and Alembic are the persistence/migration layers.

## UI detail
See `.ai/UI_STYLE_GUIDE.md` for layout dimensions, colors, typography, component patterns, table behavior, responsive rules and AI reconstruction steps.

## Navigation discrepancy to resolve
Current `frontend/src/services/sidebar.js` uses the nested label **Vulnerability Register**. The project owner's intended label is **Vulnerabilities**. If working on navigation, update the label intentionally and verify active-state behavior; do not rename the HTML route/file without a reason.

## Threat Intelligence intended workflow
Configured public Telegram channels are scanned for CVE references. Scan results retain source context and should be reviewed by an administrator. Accepted items are enriched using NVD information before promotion to the approved intelligence/register inventory. Verify every workflow step against actual routes/services before claiming it works. Jira issue creation remains a target integration unless proven implemented.

## Runtime data safety
`backend/data/` is local runtime data. Do not delete it, include it in commits, or replace the database as a troubleshooting shortcut.

## Local verification status
The user confirmed that the current web UI reflected the Table Setting label after aligning local `develop` with `origin/develop`. This confirms that specific label change was visible; it does not establish that every page/workflow has been regression-tested.

## Next priorities
1. Inspect and reconcile the Vulnerabilities sidebar label.
2. Verify Telegram scan, CVE extraction, result intake timestamp and source-message retention.
3. Verify accept/reject review and NVD enrichment end to end.
4. Verify approved findings appear in the intended inventory.
5. Verify error, empty and progress states.
6. Update this file after testing, not from assumptions.
