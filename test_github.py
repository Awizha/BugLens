import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from github_source import parse_github_url, read_github_issue
from project_tools import ProjectTools
from repository_download import (
    downloaded_repository,
    extract_python_files,
)


def make_archive(files):
    """Build a small ZIP in memory for a test."""
    archive = io.BytesIO()

    with zipfile.ZipFile(archive, "w") as zipped:
        for name, contents in files.items():
            zipped.writestr(name, contents)

    archive.seek(0)
    return archive


class GitHubTests(unittest.TestCase):
    def test_repository_and_issue_urls(self):
        self.assertEqual(
            parse_github_url("https://github.com/Awizha/issue-investigator.git"),
            ("Awizha", "issue-investigator", None),
        )
        self.assertEqual(
            parse_github_url(
                "https://github.com/Awizha/issue-investigator/issues/1"
            ),
            ("Awizha", "issue-investigator", 1),
        )

    def test_rejects_invalid_urls(self):
        invalid_urls = [
            "https://example.com/owner/repository",
            "https://github.com.evil.example/owner/repository",
            "http://github.com/owner/repository",
            "https://github.com/owner",
            "https://github.com/owner/repository/issues/zero",
            "https://github.com/owner/repository/issues/0",
            "https://github.com/owner/repository/pull/1",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    parse_github_url(url)

    def test_imports_issue_title_and_body(self):
        # Replace the network helper with a predictable response.
        with patch("github_source.github_get_json") as fake_get:
            fake_get.return_value = {
                "title": "Empty username crashes",
                "body": "Calling get_initial('') raises IndexError.",
            }

            report = read_github_issue(
                "https://github.com/owner/repository/issues/12"
            )

            self.assertEqual(
                report,
                "Empty username crashes\n\n"
                "Calling get_initial('') raises IndexError.",
            )
            fake_get.assert_called_once_with(
                "repos/owner/repository/issues/12"
            )

    def test_rejects_pull_request_response(self):
        with patch("github_source.github_get_json") as fake_get:
            fake_get.return_value = {
                "title": "A pull request",
                "body": "",
                "pull_request": {},
            }

            with self.assertRaises(ValueError):
                read_github_issue(
                    "https://github.com/owner/repository/issues/12"
                )

    def test_extracts_only_permitted_source_files(self):
        archive = make_archive({
            "snapshot/main.py": "print('hello')\n",
            "snapshot/nested/helper.py": "value = 1\n",
            "snapshot/.env": "FAKE_KEY=test",
            "snapshot/.hidden/private.py": "secret = 1",
            "snapshot/venv/library.py": "value = 2",
            "snapshot/README.md": "Example project",
        })

        with archive, tempfile.TemporaryDirectory() as folder:
            extract_python_files(archive, folder)

            files = sorted(
                path.relative_to(folder).as_posix()
                for path in Path(folder).rglob("*")
                if path.is_file()
            )

            self.assertEqual(files, ["main.py", "nested/helper.py"])
            self.assertEqual(
                (Path(folder) / "main.py").read_text(),
                "print('hello')\n",
            )

    def test_rejects_archive_path_escape(self):
        archive = make_archive({
            "snapshot/../escape.py": "print('outside')",
        })

        with archive, tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                extract_python_files(archive, folder)

    def test_rejects_oversized_python_file(self):
        archive = make_archive({
            "snapshot/large.py": "x" * 100_001,
        })

        with archive, tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                extract_python_files(archive, folder)

    def test_rejects_repository_without_python(self):
        archive = make_archive({
            "snapshot/README.md": "No Python here",
        })

        with archive, tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                extract_python_files(archive, folder)

    def test_projects_are_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()

            (first / "main.py").write_text("value = 'first'\n")
            (second / "main.py").write_text("value = 'second'\n")

            first_tools = ProjectTools(first)
            second_tools = ProjectTools(second)

            self.assertEqual(
                first_tools.read_code("main.py"),
                "1: value = 'first'",
            )
            self.assertEqual(
                second_tools.read_code("main.py"),
                "1: value = 'second'",
            )
            self.assertIn(
                "Access denied",
                first_tools.read_code("../second/main.py"),
            )
            self.assertIn(
                "Access denied",
                first_tools.read_code(str(second / "main.py")),
            )

    def test_download_cleanup_when_investigation_fails(self):
        archive = make_archive({
            "snapshot/main.py": "value = 1\n",
        })
        commit = "a" * 40

        with (
            patch("repository_download.github_get_json") as fake_get,
            patch(
                "repository_download.download_archive",
                return_value=archive,
            ),
        ):
            fake_get.side_effect = [
                {"default_branch": "main"},
                {"sha": commit},
            ]

            with self.assertRaisesRegex(RuntimeError, "Test failure"):
                with downloaded_repository(
                    "https://github.com/owner/repository"
                ) as (folder, downloaded_commit):
                    saved_folder = folder
                    self.assertTrue(folder.exists())
                    self.assertEqual(downloaded_commit, commit)

                    # Simulate something failing during the investigation.
                    raise RuntimeError("Test failure")

            self.assertFalse(saved_folder.exists())


if __name__ == "__main__":
    unittest.main()