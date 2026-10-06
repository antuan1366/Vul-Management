# TODO

## Current Release Candidate
Version: 2.0.0

### Release Gate
- [ ] Start backend successfully
- [ ] Confirm SQLite DB file is created
- [ ] Confirm schema version 5
- [ ] Confirm clean development data after migration
- [ ] Verify all asset CRUD pages
- [ ] Verify CPE/PURL extraction
- [ ] Verify NVD discovery
- [ ] Verify OSV discovery for libraries
- [ ] Verify Candidate -> Pending Review workflow
- [ ] Verify finding status badges
- [ ] Verify Approve workflow
- [ ] Verify Reject workflow
- [ ] Verify daily scan scheduling
- [ ] Verify Last Scan / Next Scan / Scan Status
- [ ] Verify Scan Now
- [ ] Verify CISA KEV enrichment
- [ ] Verify standalone Sync Status page is removed
- [ ] Verify NVD Days Back is removed from the UI
- [ ] Verify remediation status API
- [ ] Update documentation after final fixes
- [ ] User approval
- [ ] Prepare PR to main
- [ ] User performs merge
- [ ] Tag v2.0.0

### Vulnerability Intelligence
- [x] NVD CPE feed
- [x] NVD CVE feed
- [x] CISA KEV feed
- [x] Feed administration
- [x] Security identifiers
- [x] NVD CPE-to-CVE correlation
- [x] NVD applicability/version-range foundation
- [x] Incremental NVD synchronization
- [x] OSV PURL synchronization
- [x] Asset-level vulnerability synchronization
- [ ] Automatic CPE resolver confidence workflow
- [ ] Manual applicability override UI

### Vulnerability Management
- [x] Vulnerability model
- [x] Asset/Vulnerability mapping
- [x] Remediation status API
- [x] Vulnerability inventory UI
- [x] Candidate review states
- [ ] Full vulnerability detail page
- [ ] Remediation UI
- [ ] Remediation SLA/dates
- [ ] Analyst workflow

### Scanning
- [x] Daily NVD discovery schedule
- [x] Manual NVD discovery
- [x] Scan status on Vulnerabilities page
- [ ] Nessus import
- [ ] Finding normalization
- [ ] Asset matching
- [ ] Vulnerability matching
- [ ] Scan history
- [ ] Scan result UI

### Risk
- [ ] Risk calculation
- [ ] Asset criticality weighting
- [ ] CVSS weighting
- [ ] KEV weighting
- [ ] Exposure weighting
- [ ] Environment weighting
- [ ] Explainable risk score

### Reporting
- [ ] Dashboard metrics
- [ ] Vulnerability reports
- [ ] Remediation reports
- [ ] CSV/JSON export
- [ ] Trend reporting

### Security
- [ ] Authentication
- [ ] Authorization
- [ ] RBAC
- [ ] Audit logging
- [ ] API protection
- [ ] Production security review

### Future
- [ ] Optional AI/Mem0


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
