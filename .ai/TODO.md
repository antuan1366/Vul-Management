# TODO

## Current Release Candidate
Version: 2.0.0

### Release Gate
- [ ] Start backend successfully
- [ ] Confirm SQLite DB file is created
- [ ] Confirm schema version 4
- [ ] Confirm clean development data after migration
- [ ] Verify all asset CRUD pages
- [ ] Verify CPE/PURL extraction
- [ ] Verify NVD discovery with five-day default
- [ ] Verify OSV discovery for libraries
- [ ] Verify Candidate -> Pending Review workflow
- [ ] Verify Approve workflow
- [ ] Verify Reject workflow
- [ ] Verify CISA KEV enrichment
- [ ] Verify Sync Status progress
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
- [ ] Full vulnerability detail page
- [ ] Remediation UI
- [ ] Remediation SLA/dates
- [ ] Analyst workflow

### Scanning
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
