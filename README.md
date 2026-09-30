# Issue Investigator

A Python command-line agent that investigates bug reports by inspecting a local Python project. It uses OpenRouter to choose tools, gather code evidence, and suggest an explanation and fix.

The agent recommends changes; it does not modify or execute the inspected code.

## How it works

1. The user describes a bug.
2. The model requests tools to list Python files, read numbered source code, or search for keywords.
3. Python runs the requested tools and returns their results to the model.
4. The model continues investigating or returns its findings.

Investigations are limited to eight model requests and twelve tool calls.

## Features

- Searches Python files, including files in subfolders.
- Reads source code with line numbers.
- Investigates issues spanning multiple files.
- Produces suggested fixes and tests with supporting code references.
- Prompts the model to acknowledge missing evidence.
- Restricts file access to the `sample_project` directory.
- Handles common file errors, connection failures, and API rate limits.

## Setup

Developed and tested with Python 3.12.

Download or clone this repository, then open a terminal in its root directory.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Or on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to a new file named `.env` and replace the placeholder with your OpenRouter API key:

```dotenv
OPENROUTER_API_KEY=your_key_here
```

Never commit your actual API key.

## Run

From the repository root:

```bash
python investigate.py
```

Example bug reports:

```text
The app crashes when the username is empty.
```

```text
A checkout for a £100 item should apply a 20% discount and return £80, but checkout_total(100) returns £99.80. Why?
```

The files in `sample_project` contain intentional bugs for demonstrating the investigator.

## Example investigation

For the checkout report, one observed run:

1. Listed the Python files.
2. Read `checkout.py` and `discounts.py`.
3. Identified that checkout passed `0.20`, while the discount function divided its argument by `100`.
4. Suggested passing `20` to represent a 20% discount.

The investigator explained the calculation:

```text
100 × (1 − 0.20 / 100) = 99.80
100 × (1 − 20 / 100) = 80.00
```

This was a suggested correction, not a fix executed by the agent.

## Tests

Run the automated tool tests:

```bash
python -m unittest test_tools -v
```

Tests use temporary files and do not make API requests. They cover file discovery, numbered reading, searching, error handling, tool dispatch, and attempts to access files outside the permitted folder.

Three scenarios have also been checked manually through OpenRouter:

- An empty-username crash.
- A discount calculation bug spanning two files.
- A password-reset report whose relevant code was absent.

These are demonstration checks, not a broad accuracy benchmark.

## Project files

| File | Purpose |
|---|---|
| `investigate.py` | Runs the AI investigation loop. |
| `tools.py` | Implements file tools, path checks, and tool dispatch. |
| `tool_specs.py` | Describes the tools and their arguments. |
| `test_tools.py` | Tests the local tools without API calls. |
| `main.py` | Earlier manual interface for exploring the tools. |
| `sample_project/` | Small demonstration project with intentional bugs. |

## Limitations

- Currently restricted to Python files under `sample_project`.
- Uses `openrouter/free`, so the selected model and results can vary.
- Free API availability and rate limits can interrupt investigations.
- Source code returned by tools is sent to OpenRouter and its selected provider. Use demonstration code you are comfortable sharing.
- The model can make incorrect claims, cite inaccurate lines, or perform unnecessary searches.
- Suggested fixes and tests require human review.
- The agent does not run tests, apply patches, or verify its proposed fixes.
- Path restrictions are a basic access boundary, not a hardened sandbox.

## Planned improvements

- Evaluate against a larger set of known bugs.
- Compare tool-based investigation with sending all source code in one request.
- Record the selected model and request usage.
- Test the investigation loop with simulated API responses.
- Improve handling of redundant tool requests.