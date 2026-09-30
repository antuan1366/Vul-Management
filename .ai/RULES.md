# RULES

## Development Rules

1. Do not rewrite unrelated parts of the project.

2. Keep backend services modular.

3. Keep API routes separate from business logic.

4. Keep frontend pages modular.

5. Prefer separate files for separate functionality.

6. Do not put the entire frontend into one large HTML file.

7. When changing an existing file during development, provide the complete
replacement file rather than partial edits.

8. Test the application after significant changes.

9. Do not push to GitHub without explicit approval.

10. GitHub should contain reviewed milestones.

## AI Development Rules

An AI working on this project should:

- Read START_HERE.md first.
- Read STATE.md before changing existing functionality.
- Read ARCHITECTURE.md before changing architecture.
- Read DECISIONS.md before introducing major architectural changes.
- Read TODO.md to understand current priorities.
- Respect existing decisions unless the user explicitly changes them.

## Scope Rules

Do not introduce AI/Mem0/Gemini functionality unless explicitly requested.

Do not introduce unnecessary frameworks or dependencies.

Prefer simple solutions during early development.

## Database Rules

Database schema changes must be deliberate.

Do not silently delete existing data.

Do not recreate the database merely to solve a schema problem.

## Security Rules

Never commit:

- passwords
- API keys
- tokens
- private keys
- .env secrets
- production credentials

## Git Rules

Before commit:

- inspect git status
- inspect staged files
- verify secrets are not included

Use meaningful commit messages.

Use version tags for significant releases.
