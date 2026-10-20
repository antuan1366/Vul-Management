# STRATEGY

## Guiding principles
Develop Vul-Management incrementally and keep the product operational and understandable.

For each meaningful change:
1. Read relevant .ai/ notes and inspect real source/API/database contracts.
2. Define intended behavior and affected pages.
3. Implement the smallest coherent change.
4. Run relevant tests; record what passed and what could not be run.
5. Review changes and protect user data/secrets.
6. Update .ai/ documentation.
7. Commit on develop or a focused branch.
8. Merge to main only after explicit user authorization; use a pull request and verify its result.

## Current version/promotion
- Version selected for current promotion: 3.6.5.
- Schema remains 11; latest migration is 0011. The version bump and inventory-based Scan Result matching do not introduce a migration.
- Current source includes local authentication/user administration, Vulnerability Register custom fields, combined product/version display, NVD-first supplemental CVE lookup and advisory asset-message matching.
- Do not describe 3.6.5 as production-verified until outstanding automated, migration, browser and workflow tests are complete.

## Current priorities
1. Confirm the GitHub develop-to-main merge for 3.6.5 and version declarations on both branches.
2. Run asset-message matching unit tests and verify representative positive/negative cases.
3. Back up a test database and validate migration 0011 and existing-data compatibility.
4. Verify authentication, account roles and protected routes.
5. Test Vulnerability Register custom fields and Scan Result layout/preferences.
6. Exercise Telegram discovery, NVD/supplemental enrichment, review/promotion and source provenance end to end.
7. Exercise Nessus XML import, finding review, deduplication and host mapping.
8. Test Jira against a non-production project.
9. Build and test a clean customer deployment package.

## Product principles
- Asset inventory is administrator-managed. Do not make external CPE discovery a required prerequisite for asset entry.
- Keep raw external findings separate from approved vulnerability inventory.
- A message-to-asset match is only an attention hint, not confirmed vulnerability applicability.
- Jira and other integrations must not be presented as validated until tested end to end.
- Core functionality must work without AI.
