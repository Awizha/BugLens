import re
from urllib.parse import urlsplit

import requests

#parse_github_url() checks the URL and extracts the owner, repository, 
# and issue number.
def parse_github_url(url):
    """Return the owner, repository name, and optional issue number."""

    parsed = urlsplit(url.strip())

    # Accept ordinary HTTPS GitHub links only.
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError("Use an HTTPS URL from github.com.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) not in (2, 4):
        raise ValueError("Enter a repository URL or a GitHub issue URL.")

    owner = parts[0]
    repository = parts[1].removesuffix(".git")

    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise ValueError("Invalid GitHub owner name.")

    if (
        not re.fullmatch(r"[A-Za-z0-9_.-]+", repository)
        or repository in (".", "..")
    ):
        raise ValueError("Invalid repository name.")

    issue_number = None

    if len(parts) == 4:
        if parts[2] != "issues" or not re.fullmatch(r"[0-9]+", parts[3]):
            raise ValueError("Expected an issue URL ending in /issues/NUMBER.")

        issue_number = int(parts[3])

        if issue_number < 1:
            raise ValueError("The issue number must be positive.")

    return owner, repository, issue_number

#github_get_json() requests public GitHub data and handles common errors.
def github_get_json(api_path):
    """Read public data from GitHub's API."""

    url = f"https://api.github.com/{api_path}"

    try:
        response = requests.get(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "issue-investigator",
            },
            timeout=30,
            allow_redirects=False,
        )
    except requests.exceptions.RequestException as error:
        raise ValueError("Could not connect to GitHub. Try again later.") from error

    if response.status_code == 404:
        raise ValueError("GitHub could not find this public repository or issue.")

    if response.status_code in (403, 429):
        raise ValueError(
            "GitHub denied the request or its API limit was reached. "
            "Try again later."
        )

    if 300 <= response.status_code < 400:
        raise ValueError(
            "This GitHub address has moved. Use the repository's current URL."
        )

    if response.status_code != 200:
        raise ValueError(f"GitHub returned HTTP {response.status_code}.")

    try:
        data = response.json()
    except ValueError as error:
        raise ValueError("GitHub returned an unreadable response.") from error

    if not isinstance(data, dict):
        raise ValueError("GitHub returned an unexpected response.")

    return data

#read_github_issue() turns an issue’s title and description into 
# the text our agent will investigate. It doesn’t import comments yet.
def read_github_issue(issue_url):
    """Get an issue's title and description as a bug report."""

    owner, repository, issue_number = parse_github_url(issue_url)

    if issue_number is None:
        raise ValueError("Provide an issue URL ending in /issues/NUMBER.")

    data = github_get_json(
        f"repos/{owner}/{repository}/issues/{issue_number}"
    )

    # GitHub's issue API can also return pull requests.
    if "pull_request" in data:
        raise ValueError("Provide a bug issue rather than a pull request.")

    title = data.get("title")
    body = data.get("body") or ""

    if not isinstance(title, str) or not isinstance(body, str):
        raise ValueError("GitHub returned an invalid issue title or description.")

    report = f"{title}\n\n{body}".strip()

    if len(report) > 20_000:
        raise ValueError(
            "This issue is too long. Use a repository URL and a shorter "
            "bug description instead."
        )

    return report