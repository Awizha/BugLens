from pathlib import Path


class ProjectTools:
    def __init__(self, project_folder):
        # Each instance remembers the one folder it may inspect.
        self.root = Path(project_folder).resolve()

        if not self.root.is_dir():
            raise ValueError("The project folder does not exist.")

        self.available_tools = {
            "list_python_files": self.list_python_files,
            "read_code": self.read_code,
            "search_code": self.search_code,
        }

    def checked_path(self, file_path):
        path = (self.root / file_path).resolve()

        if not path.is_relative_to(self.root):
            raise ValueError("Access denied: stay inside this project.")

        # Exclude hidden files and common dependency/cache folders.
        excluded = {"venv", "node_modules", "__pycache__"}

        for part in path.relative_to(self.root).parts:
            if part.startswith(".") or part in excluded:
                raise ValueError("Access denied: this path is excluded.")

        return path

    def read_code(self, file_path):
        try:
            path = self.checked_path(file_path)

            if path.suffix != ".py":
                return "Error: only Python source files can be read."

            # Avoid sending very large files to the model.
            if path.stat().st_size > 100_000:
                return "Error: file exceeds the 100 KB reading limit."

            code = path.read_text(encoding="utf-8")

        except (OSError, ValueError) as error:
            return f"Error: {error}"

        numbered_lines = []

        for number, line in enumerate(code.splitlines(), start=1):
            numbered_lines.append(f"{number}: {line}")

        return "\n".join(numbered_lines)

    def list_python_files(self, folder_path="."):
        folder = self.checked_path(folder_path)

        if not folder.is_dir():
            raise ValueError("Expected an existing project folder.")

        files = set()

        for candidate in folder.rglob("*.py"):
            try:
                path = self.checked_path(candidate)
            except ValueError:
                continue

            if path.is_file():
                # Return paths relative to this project, not your computer.
                files.add(path.relative_to(self.root).as_posix())

        return sorted(files)

    def search_code(self, folder_path, keyword):
        if not keyword.strip():
            return ["Error: please provide a search keyword."]

        matches = []

        for file_path in self.list_python_files(folder_path):
            # Reuse the same path, file-type, and size checks as reading.
            numbered_code = self.read_code(file_path)

            if numbered_code.startswith("Error:"):
                matches.append(f"{file_path}: {numbered_code}")
                continue

            for numbered_line in numbered_code.splitlines():
                number, line = numbered_line.split(": ", 1)

                if keyword in line:
                    matches.append(
                        f"{file_path}:{number}: {line.strip()}"
                    )

        return matches

    def execute_tool(self, tool_name, arguments):
        if tool_name not in self.available_tools:
            return f"Error: unknown tool '{tool_name}'."

        function = self.available_tools[tool_name]

        try:
            result = function(**arguments)
        except (ValueError, TypeError, OSError) as error:
            return f"Error: {error}"

        if isinstance(result, list):
            return "\n".join(str(item) for item in result) or "No results found."

        return str(result)