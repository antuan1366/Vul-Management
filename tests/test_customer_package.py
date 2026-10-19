import unittest
from pathlib import Path

from scripts.build_customer_package import should_exclude, validate_env_template


class CustomerPackageRulesTests(unittest.TestCase):
    def test_excludes_local_environment_files_and_backups(self):
        for path in (
            ".env",
            "backend/.env.backup",
            "backend/.env.local",
            "backend/data/local.db",
        ):
            with self.subTest(path=path):
                self.assertTrue(should_exclude(Path(path)))

    def test_keeps_reviewed_environment_template(self):
        self.assertFalse(should_exclude(Path("backend/.env.example")))

    def test_excludes_database_sidecars_logs_and_sessions_case_insensitively(self):
        for path in (
            "backend/data/vul_management.DB",
            "backend/data/vul_management.db-wal",
            "backend/logs/app.LOG",
            "backend/data/telegram.SESSION",
            "backend/data/telegram.session-journal",
        ):
            with self.subTest(path=path):
                self.assertTrue(should_exclude(Path(path)))

    def test_excludes_private_key_and_common_secret_files(self):
        for path in (
            "deploy/server.key",
            "deploy/client.PEM",
            "credentials.json",
            "secrets.json",
            "token.json",
            "id_rsa",
        ):
            with self.subTest(path=path):
                self.assertTrue(should_exclude(Path(path)))

    def test_keeps_application_source(self):
        for path in (
            "backend/app/main.py",
            "frontend/src/pages/dashboard.html",
            "backend/.env.example",
        ):
            with self.subTest(path=path):
                self.assertFalse(should_exclude(Path(path)))

    def test_accepts_empty_credentials_in_template(self):
        validate_env_template(
            "TELEGRAM_API_ID=\nTELEGRAM_API_HASH=\nJIRA_API_TOKEN=\n"
        )

    def test_rejects_non_empty_credential_in_template(self):
        with self.assertRaisesRegex(ValueError, "JIRA_API_TOKEN"):
            validate_env_template("JIRA_API_TOKEN=not-a-real-token\n")


if __name__ == "__main__":
    unittest.main()
