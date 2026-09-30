import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tools


class ToolTests(unittest.TestCase):
    def setUp(self):
        # Use a temporary project so tests don't change your sample files.
        temporary_folder = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_folder.cleanup)

        self.root = Path(temporary_folder.name).resolve()
        self.project = self.root / "sample_project"
        self.project.mkdir()

        # Point the tools at our temporary project during each test.
        settings = patch.multiple(
            tools,
            PROJECT_ROOT=self.root,
            ALLOWED_FOLDER=self.project,
        )
        settings.start()
        self.addCleanup(settings.stop)

        (self.project / "first.py").write_text(
            "username = 'Alex'\nprint(username)\n",
            encoding="utf-8",
        )

        nested = self.project / "nested"
        nested.mkdir()

        (nested / "second.py").write_text(
            "username = ''\n",
            encoding="utf-8",
        )

        (self.project / "notes.txt").write_text(
            "Not Python code.",
            encoding="utf-8",
        )

    def test_read_code_numbers_lines(self):
        result = tools.read_code("sample_project/first.py")

        self.assertEqual(
            result,
            "1: username = 'Alex'\n2: print(username)",
        )

    def test_lists_python_files_in_subfolders(self):
        result = tools.list_python_files("sample_project")

        self.assertEqual(
            result,
            [
                self.project / "first.py",
                self.project / "nested" / "second.py",
            ],
        )

    def test_search_checks_both_files(self):
        result = tools.search_code("sample_project", "username")

        self.assertEqual(
            result,
            [
                f"{self.project / 'first.py'}:1: username = 'Alex'",
                f"{self.project / 'first.py'}:2: print(username)",
                f"{self.project / 'nested' / 'second.py'}:1: username = ''",
            ],
        )

    def test_read_errors(self):
        self.assertIn(
            "file not found",
            tools.read_code("sample_project/missing.py"),
        )
        self.assertIn(
            "expected a file",
            tools.read_code("sample_project"),
        )

        # These bytes cannot be decoded as UTF-8 text.
        (self.project / "invalid.py").write_bytes(b"\xff")

        self.assertIn(
            "could not read this file as UTF-8",
            tools.read_code("sample_project/invalid.py"),
        )

    def test_blocks_paths_outside_project(self):
        # This is fake data, not your real API key.
        secret = self.root / ".env"
        secret.write_text("FAKE_SECRET=test", encoding="utf-8")

        for path in [".env", "sample_project/../.env", str(secret)]:
            with self.subTest(path=path):
                self.assertIn("Access denied", tools.read_code(path))

    def test_blocks_symlink_to_outside_file(self):
        # A symlink is a shortcut pointing to another file.
        outside = self.root / "outside.py"
        outside.write_text("secret = 'fake'\n", encoding="utf-8")

        link = self.project / "shortcut.py"
        link.symlink_to(outside)

        self.assertIn(
            "Access denied",
            tools.read_code("sample_project/shortcut.py"),
        )
        self.assertNotIn(outside, tools.list_python_files("sample_project"))
        self.assertEqual(tools.search_code("sample_project", "secret"), [])

    def test_dispatcher_handles_invalid_requests(self):
        self.assertIn(
            "unknown tool",
            tools.execute_tool("delete_file", {}),
        )
        self.assertTrue(
            tools.execute_tool("read_code", {}).startswith("Error:"),
        )
        self.assertEqual(
            tools.execute_tool(
                "search_code",
                {"folder_path": "sample_project", "keyword": "nonexistent"},
            ),
            "No results found.",
        )
        self.assertIn(
            "please provide a search keyword",
            tools.execute_tool(
                "search_code",
                {"folder_path": "sample_project", "keyword": "   "},
            ),
        )


if __name__ == "__main__":
    unittest.main()