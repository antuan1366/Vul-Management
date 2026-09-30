# DECISIONS

## Decision 001 - Core First

AI functionality is postponed.

Reason:
The primary goal is to create a reliable vulnerability management
platform before adding AI capabilities.

## Decision 002 - Modular Backend

Backend code is separated into:

- API
- Services
- Models
- Schemas
- Core

Reason:
This makes troubleshooting and future development easier.

## Decision 003 - SQLite During Early Development

SQLite is currently used.

Reason:
It provides a simple local development environment.

The architecture should allow migration to PostgreSQL later.

## Decision 004 - Separate Asset Types

Assets are divided into:

1. Equipment
2. Operating System
3. Applications
4. Libraries

Reason:
Different asset types require different attributes and vulnerability
mapping logic.

## Decision 005 - Git Release Discipline

GitHub should contain approved development milestones rather than every
experimental change.

The user reviews the application before major commits.

## Decision 006 - Project Memory

.ai files are used to preserve project context for future AI sessions.

Git history remains responsible for code history.

.ai is responsible for:
- project context
- architecture
- strategy
- current state
- decisions
- rules
- next tasks
