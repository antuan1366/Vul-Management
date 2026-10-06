# DECISIONS

## Decision 001 - Core First

AI functionality is postponed.

Reason:
The primary goal is a reliable vulnerability management platform before
adding AI capabilities.

## Decision 002 - Modular Backend

Backend code is separated into:
- API
- Services
- Models
- Schemas
- Core

Reason:
This improves troubleshooting and future development.

## Decision 003 - SQLite Single-File Database

SQLite is the current application database.

Reason:
It provides a real SQL database while keeping the complete database in one
portable file.

Default:
backend/data/vul_management.db

SQLAlchemy is the data-access layer and Alembic manages schema changes.

The database engine remains replaceable for a future PostgreSQL deployment.

## Decision 004 - Separate Asset Types

Assets are divided into:
1. Equipment
2. Operating System
3. Applications
4. Libraries

Reason:
Different asset types require different attributes and vulnerability mapping
logic.

## Decision 005 - Candidate Before Approval

External vulnerability discovery must create a Vulnerability Candidate first.

Only an administrator review can promote a candidate into the approved
Vulnerability inventory.

Reason:
External intelligence is evidence, not automatically trusted inventory.

## Decision 006 - CISA KEV Enriches Approved Inventory

CISA KEV should enrich approved vulnerability records rather than bypassing
the review workflow.

## Decision 007 - Git Release Discipline

GitHub should contain reviewed development milestones.

The user reviews the application before major commits and performs merges.

## Decision 008 - Project Memory

.ai files preserve project context for future AI sessions.

Git history remains responsible for code history.

.ai is responsible for:
- project context
- architecture
- strategy
- current state
- decisions
- rules
- next tasks
- compatibility notes

## Decision 009 - Major Release Gate

Version 2.0.0 is a release candidate until local API/UI verification is
complete and the user explicitly approves promotion to main.


## Decision 010 - Online Asset Identification

Asset administrators should enter only the information they already know. Vul-Management performs online identification for each asset category.

Equipment, Operating Systems and Applications use NVD CPE resolution. Libraries use PURL because package ecosystems are better represented by package identifiers than by forcing CPE matching.

Automatic matches remain pending administrator verification. Reasons and candidate matches are stored so an administrator can understand and correct failed or ambiguous identification.

NVD CPE and OSV endpoints are configured as Feeds and can be connectivity-tested from Administration > Feeds.
