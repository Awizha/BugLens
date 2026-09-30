from pathlib import Path






# Restrict file access to sample_project so the AI cannot read .env and the API key
PROJECT_ROOT = Path(__file__).resolve().parent
ALLOWED_FOLDER = (PROJECT_ROOT / "sample_project").resolve()
def checked_path(file_path):
    path = (PROJECT_ROOT / file_path).resolve()

    if not path.is_relative_to(ALLOWED_FOLDER):
        raise ValueError("Access denied: stay inside sample_project.")
    return path




def read_code(file_path):
    try:
        path = checked_path(file_path)
        #read_text method reads a file as a text
        code = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Error: file not found: {file_path}"
    except IsADirectoryError:
        return f"Error: expected a file, but got a folder: {file_path}"
    except PermissionError:
        return f"Error: permission denied: {file_path}"
    except UnicodeDecodeError:
        return f"Error: could not read this file as UTF-8 text: {file_path}"
    except ValueError as error:
            return str(error)

    lines = code.splitlines()
    numbered_lines = []

    for number, line in enumerate(lines, start=1):
        numbered_lines.append(f"{number}: {line}")

    return "\n".join(numbered_lines)


def list_python_files(folder_path):
    folder = checked_path(folder_path)
    files = []
    for file in sorted(folder.rglob("*.py")):
        try:
            safe_path = checked_path(file)
        except ValueError:
            continue

        if safe_path.is_file():
            files.append(safe_path)

    return files
    

def search_code(folder_path, keyword):
    if not keyword.strip():
        return ["Error: please provide a search keyword."]

    matches = []

    try:
        files = list_python_files(folder_path)
    except ValueError as error:
        return [str(error)]

    for file in files:
        try:
            path = checked_path(file)
            lines = path.read_text(encoding="utf-8").splitlines()
        except (ValueError, OSError, UnicodeDecodeError) as error:
            matches.append(f"Could not search {file}: {error}")
            continue

        for number, line in enumerate(lines, start=1):
            if keyword in line:
                matches.append(f"{file}:{number}: {line.strip()}")

    return matches



AVAILABLE_TOOLS = {
    "list_python_files": list_python_files,
    "read_code": read_code,
    "search_code": search_code,
}


def execute_tool(tool_name, arguments):
    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: unknown tool '{tool_name}'."

    function = AVAILABLE_TOOLS[tool_name]

    try:
        result = function(**arguments)
    except (ValueError, TypeError, OSError) as error:
        return f"Error: {error}"

    #if result is a list, turn it into text and send back to the AI
    if isinstance(result, list):
        return "\n".join(str(item) for item in result) or "No results found."

    return str(result)
