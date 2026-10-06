# STATE

## Version
2.0.0 release candidate

## State
VULNERABILITY INTELLIGENCE + APPROVAL WORKFLOW + SCHEDULED SCANNING + SQLITE FOUNDATION

The current candidate is based on the approved-findings/sync-status feature line and is being prepared as the next major release.

## Implemented

- Asset Management: Equipment, Operating Systems, Applications, Libraries
- Generic Asset Fields
- Feed Administration
- NVD CPE resolution
- NVD CVE discovery
- CPE applicability/version evaluation foundation
- OSV PURL synchronization
- Security Identifier storage
- Vulnerability Candidate storage
- Candidate approve/reject workflow
- Approved Vulnerability inventory
- Asset/Vulnerability mapping
- CISA KEV enrichment
- Remediation status API
- Asset identifier extraction
- Sync Jobs with progress/status
- Daily vulnerability scan scheduling
- Last/next scan status on the Vulnerabilities page
- Unified vulnerability finding status on the Vulnerabilities page
- SQLite single-file database

## Vulnerability Workflow

Asset
-> Vendor/Product/Version
-> CPE or PURL
-> NVD / OSV
-> Applicability evaluation
-> Vulnerability Candidate
-> Pending Review
-> Administrator action
-> Approved / Rejected
-> Asset/Vulnerability mapping
-> CISA KEV
-> Remediation

A CPE match alone is not automatically treated as a confirmed approved vulnerability.

## Scan Workflow

The Vulnerabilities page is the control point for vulnerability discovery.

- Scan Now starts NVD candidate discovery.
- The administrator can enable a daily scan at a selected HH:MM time.
- Last scan, next scan and scan status are shown on the same page.
- The old standalone Sync Status page is removed from the UI.
- The NVD look-back value is no longer exposed in the Vulnerabilities UI; the current internal discovery window remains five days.

## Database

Engine:
- SQLite

Database file:
- backend/data/vul_management.db

Alembic revisions:
- 0001 baseline
- 0002 vulnerability intelligence
- 0003 feed synchronization metadata
- 0004 candidate workflow and sync jobs
- 0005 vulnerability scan schedule

Supported schema:
- 1-5

The local database file is ignored by Git.

## Git

Current branch:
feature/v2-sqlite-foundation

Base:
feature/approved-findings-sync-status

This branch is a release-candidate preparation branch. It must not be merged automatically.

The user performs local verification and the final merge.

## Immediate Verification

1. Start backend successfully.
2. Confirm database bootstrap and schema 5.
3. Confirm the scan schedule is created with scheduling disabled by default.
4. Open Vulnerabilities and confirm the discovery status panel is visible.
5. Run Scan Now and confirm Last Scan/Scan Status update.
6. Enable a daily schedule and verify Next Scan is populated.
7. Create test assets.
8. Extract CPE/PURL identifiers.
9. Run NVD/OSV discovery.
10. Confirm discoveries appear as Pending Review.
11. Approve one candidate and reject another.
12. Confirm statuses are visible in the single findings table.
13. Confirm only approved findings enter the approved inventory.
14. Verify CISA KEV enriches approved findings.
15. Verify the old Sync Status page/link is gone.
16. Verify the SQLite file is created under backend/data.


## Latest Vulnerability Scan UX Update

- The Vulnerabilities page now has a single **Scan** button in the upper-right.
- The Scan menu contains:
  - One-time Scan
  - Scheduled Scan
- Scheduled Scan configuration is revealed from the same menu instead of being permanently displayed.
- Vulnerability findings remain on the Vulnerabilities page and are tied to the asset inventory.
- The standalone Scan Results navigation item was removed.
- A scan first evaluates the current asset inventory and refreshes CPE identifiers before NVD discovery.
- If the asset inventory is empty, the scan completes with a `no_assets` state and a clear message that the scan started but no assets are defined.
- If assets exist but none has a resolved CPE, the scan completes with a `no_scannable_assets` state.
- The scan status API exposes the last job result so the Vulnerabilities page can show the scan outcome directly.
