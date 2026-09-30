# BugLens 🔎

An AI-assisted bug investigator for Python projects, with a local web interface and GitHub integration.

Give BugLens a public GitHub repository and a bug description—or a GitHub issue URL. It inspects source code using file tools, gathers evidence, and recommends a likely cause, a fix, and a test.

**BugLens reads code. It does not execute the inspected project, apply fixes, or verify that suggested fixes work.**

## Features

- **GitHub repository import:** downloads a snapshot of the repository’s default branch.
- **GitHub issue import:** reads an issue’s title and description.
- **Tool-driven investigation:** the model chooses when to list files, read code, and search for keywords.
- **Source references:** numbered code helps the model cite supporting files and lines.
- **Web and terminal interfaces:** use the Streamlit app or investigate the local sample project from the terminal.
- **Progress display:** see investigation rounds and tool requests.
- **Project isolation:** each investigation’s tools are restricted to its selected folder.
- **Bounded investigations:** at most eight model requests and twelve tool calls.
- **Temporary downloads:** downloaded source files are removed when the download context exits.

## How it works

```text
Repository URL + bug description
             OR
        GitHub issue URL
              ↓
    Import the bug report
              ↓
Download a repository snapshot
              ↓
    AI requests a file tool
              ↓
Python runs the tool and returns its result
              ↓
 Repeat until findings or a limit is reached
              ↓
 Display recommendations and remove temporary files
```

The model requests tools; Python executes those requests through an allowed tool registry.

Available tools:

| Tool | Purpose |
|---|---|
| `list_python_files` | Find Python files in the selected project. |
| `read_code` | Read a Python file with numbered lines. |
| `search_code` | Find lines containing a keyword across Python files. |

The web and terminal interfaces share the investigation function in `agent.py`.

## Tech stack

- Python 3.12
- Streamlit
- OpenRouter
- Requests
- python-dotenv
- Python’s built-in `unittest` framework

The current model setting is `openrouter/free`. The underlying model can vary between requests, so results are not guaranteed to be consistent.

## Setup

### 1. Download the project

Clone this repository using the URL shown in GitHub’s **Code** menu, or download and extract its ZIP archive.

Open a terminal in the project’s root directory.

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Create an API key in [OpenRouter](https://openrouter.ai/settings/keys).

Copy `.env.example` to a file named `.env`, then replace the placeholder:

```dotenv
OPENROUTER_API_KEY=your_key_here
```

Keep `.env` private. It is excluded by `.gitignore`.

An OpenRouter key is required for AI investigations. Public GitHub imports currently use unauthenticated requests; no GitHub token is required.

## Run the web interface

```bash
python -m streamlit run app.py --server.address 127.0.0.1
```

Open:

```text
http://127.0.0.1:8501
```

Keep the terminal running while using the app. Press `Ctrl+C` in that terminal to stop it.

### Investigate a repository

1. Enter a public GitHub repository URL.
2. Describe the bug, including expected and actual behaviour.
3. Click **Investigate**.
4. Review the progress and resulting recommendations.

Example report for the included sample code:

```text
In sample_project/registration.py, the app crashes when the username is empty.
```

### Investigate a GitHub issue

1. Enter a URL in this format:

   ```text
   https://github.com/OWNER/REPOSITORY/issues/NUMBER
   ```

2. Leave the bug-description field blank to use the issue’s title and description.
3. Optionally enter additional context in that field.
4. Click **Investigate**.
5. Expand **Bug report used** to inspect the imported report.

Issue comments and attachments are not imported. Pull requests are not supported as issue inputs.

The app inspects the latest commit on the repository’s default branch. It does not automatically identify the historical code version associated with an issue.

### Local hosting

The launch command binds the app to your own computer.

Publishing this repository on GitHub does not deploy the web app. Public hosting would require additional decisions about authentication, API-key management, usage limits, and concurrent requests.

## Run the terminal interface

```bash
python investigate.py
```

The terminal interface investigates the local `sample_project` folder.

Example reports:

```text
The app crashes when the username is empty.
```

```text
A checkout for a £100 item should apply a 20% discount and return £80,
but checkout_total(100) returns £99.80. Why?
```

The bugs in `sample_project` are intentional demonstration cases.

## Example finding

For the checkout report, an observed investigation connected two files:

- `checkout.py` passed `0.20` as the discount.
- `discounts.py` divided that argument by `100`.

The agent explained the result:

```text
100 × (1 − 0.20 / 100) = 99.80
```

It recommended passing `20` to represent a 20% discount:

```text
100 × (1 − 20 / 100) = 80.00
```

This was a recommendation based on source inspection. BugLens did not execute the calculation or apply the change.

## Tests and validation

Run the automated tests:

```bash
python -m unittest test_tools test_github -v
```

The current suite contains **17 tests**, covering:

- File discovery, numbered reading, and keyword searching.
- Common file errors and invalid tool requests.
- Path traversal and symlink escape checks in the original tools.
- GitHub repository and issue URL parsing.
- Issue import using simulated GitHub responses.
- Archive filtering and rejection of unsafe paths.
- Rejection of oversized Python files and archives without supported source.
- Isolation between project-tool instances.
- Temporary-folder cleanup when an investigation raises an exception.

Tests use temporary files and mocked network helpers. They do not contact GitHub or OpenRouter.

### Manual checks completed

- Diagnosed the empty-username crash.
- Diagnosed the discount bug across two files.
- Recognised missing authentication code for an unrelated password-reset report.
- Investigated a public repository through the web interface.
- Imported a real GitHub issue and used its title and description for investigation.

These checks demonstrate selected behaviours. They are not a broad accuracy benchmark, and the investigation loop’s API handling is not yet comprehensively tested.

## Limits and data handling

| Limit | Current value |
|---|---:|
| Model requests per investigation | 8 |
| Tool calls per investigation | 12 |
| Web bug-report length | 20,000 characters |
| Repository archive download | 20 MB |
| Archive entries | 10,000 |
| Extracted Python files | 200 |
| Individual Python file | 100 KB |
| Total extracted Python source | 5 MB |

File-size limits use decimal bytes.

Only `.py` files are extracted. Hidden paths, selected dependency/cache folders, and archive links are excluded. Unsafe archive paths are rejected.

The downloader records the inspected commit identifier so a result can be associated with a particular snapshot.

**Source returned by tools and bug descriptions are sent to OpenRouter and its selected provider.** File filtering does not guarantee that Python source contains no sensitive information. Use code you are authorised and comfortable sharing.

Downloaded code is read as text, not imported or executed. The application’s own Python code and its dependencies do run locally.

## Project structure

```text
.
├── app.py
├── agent.py
├── investigate.py
├── project_tools.py
├── github_source.py
├── repository_download.py
├── tool_specs.py
├── tools.py
├── main.py
├── test_tools.py
├── test_github.py
├── requirements.txt
├── .env.example
├── .gitignore
└── sample_project/
    ├── checkout.py
    ├── discounts.py
    ├── profile.py
    └── registration.py
```

| File | Purpose |
|---|---|
| `app.py` | Streamlit interface for GitHub investigations. |
| `agent.py` | Shared AI conversation loop and progress reporting. |
| `investigate.py` | Terminal entry point. |
| `project_tools.py` | File tools restricted to one project folder. |
| `github_source.py` | GitHub URL parsing and public issue import. |
| `repository_download.py` | Repository snapshot download, filtering, and cleanup. |
| `tool_specs.py` | Tool descriptions and argument schemas sent to the model. |
| `tools.py` | Original tools for the local sample project. |
| `main.py` | Earlier manual interface for exploring the original tools. |
| `test_tools.py` | Tests for the original local tools. |
| `test_github.py` | GitHub import, archive, and project-isolation tests. |
| `sample_project/` | Small source files containing intentional demonstration bugs. |

## Known limitations

- Supports public GitHub repositories and Python source only.
- Instructions encourage evidence-based answers but cannot guarantee them.
- Search is keyword-based and case-sensitive.
- Only Python source is extracted, so relevant configuration or documentation may be absent.
- Free-model availability, model selection, and API rate limits can affect results.
- Fixes and tests require human review and execution.


## Planned improvements

- Test the investigation loop with simulated API responses.
- Evaluate against a larger collection of known bugs and publish the results.
- Validate reported code references against inspected evidence.
- Reduce redundant tool calls.