# TODO

## Current promotion: v3.6.5
- [x] Update version declarations in backend configuration, sidebar and outbound service User-Agent headers to 3.6.5.
- [x] Reconcile current .ai/ documentation with source implementation and verification status.
- [x] Document compatibility: schema max 11, migration 0011 latest, no migration for the version bump or asset matching.
- [x] Add a release note with included capabilities and known test gaps.
- [x] User explicitly authorized merging develop into main for this promotion.
- [x] Confirm GitHub reports the develop-to-main pull request as merged and verify the resulting main head contains version 3.6.5.
- [ ] Run python -m unittest discover -s tests -p test_asset_message_matching.py from the repository root and record output.
- [ ] Verify /api/info returns application version 3.6.5 and the expected schema values.
- [ ] Run regression tests for sign-in/out, session expiry, account roles and protected APIs/docs.
- [ ] Test migration 0011 on a backed-up test database; do not run it against live user data without a verified backup and plan.
- [ ] Test Vulnerability Register custom-field create/rename/required/show/delete, persistence and required validation.
- [ ] Verify combined Affected Product / Version columns and legacy table-setting migration.
- [ ] Verify Scan Result matching across all four asset categories; test custom values, IPv4, word boundaries, false positives, row highlights, details and refresh after inventory edits.
- [ ] Verify Telegram scan/scheduling, original source-message retention, review/reject, NVD and supplemental-source enrichment, and promotion using controlled data.
- [ ] Test Nessus upload and parsing with a synthetic XML fixture, finding-state changes, deduplication, CVE validation and host mapping.
- [ ] Test Jira issue creation using a non-production project and token.
- [ ] Build and verify a clean deployment package on a separate machine, including database initialization, upgrade, backup and restore.

## Earlier implementation checkpoints (verification still needed where not separately evidenced)
### Authentication and users
- [ ] Test a fresh database with no users and confirm current bootstrap behavior (admin / vulmgm); change the default before any untrusted-network exposure.
- [ ] Test valid/invalid login, logout, eight-hour session expiry, inactive-user rejection and login throttling.
- [ ] Test Admin user-management actions, duplicate-name rejection and last-active-admin protection.
- [ ] Review fine-grained authorization for asset/vulnerability actions before production use.

### Vulnerability Register custom fields — migration 0011
- [ ] Confirm a backed-up schema-10 test database upgrades to schema 11 and preserves existing data.
- [ ] Confirm a fresh database initializes/records schema 11 correctly.
- [ ] Run custom field CRUD, validation and persistence tests.

### Scan Result matching
- [ ] Confirm heuristic matches never auto-approve findings or state that an asset is definitely vulnerable.
- [ ] Record actual automated and browser test results; source review alone is not a pass.

## Deployment/product backlog
- [ ] Define supported OS and Python versions.
- [ ] Exclude local database, credentials, tokens, virtual environments, caches and Telegram session files from deployment artifacts.
- [ ] Provide a configuration template with placeholder values only.
- [ ] Document install/start/stop/upgrade, backup and restore.
- [ ] Verify the package on a separate clean machine.
- [ ] Create an immutable version tag/release only after appropriate verification and explicit release approval.
