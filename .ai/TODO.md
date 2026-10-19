# TODO

## v3.1.0 Nessus workflow
- [x] Add Nessus XML upload and explicit analysis endpoint.
- [x] Store report and plugin findings separately from CVE register data.
- [x] Add Nessus Scan Result review tabs: New, Under Review, Accept, Reject.
- [x] Promote accepted valid CVEs to the existing shared Vulnerability Register.
- [x] Block CVE-register promotion for findings without valid CVEs.
- [x] Add Administration → Nessus Host Mapping.
- [x] Add Alembic 0008 and declare application version 3.1.0/schema max 8.
- [ ] Install dependencies and run startup/migration checks.
- [ ] Test upload, analysis, review, register deduplication and host mappings with a synthetic report.
- [ ] Verify Table Setting, responsive layout and all UI actions.
- [ ] Validate parsing against a real Nessus XML report.

## Existing verification backlog
- [ ] Verify Telegram scanning, NVD enrichment, accept/reject and register promotion.
- [ ] Verify CRUD for all asset types and custom fields.
- [ ] Verify sidebar/navigation, Table Setting, pagination and responsive layout.
- [ ] Confirm no local DB, secrets, or runtime data are included in Git.
- [ ] User approves any merge to `main`.
