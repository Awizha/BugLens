import io
import re
import stat
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

import requests

from github_source import github_get_json, parse_github_url


MAX_DOWNLOAD_BYTES = 20_000_000
MAX_ARCHIVE_ENTRIES = 10_000
MAX_PYTHON_FILES = 200
MAX_FILE_BYTES = 100_000
MAX_SOURCE_BYTES = 5_000_000

EXCLUDED_FOLDERS = {"venv", "node_modules", "__pycache__"}


def download_archive(owner, repository, commit):
    """Download a bounded ZIP archive for one exact commit."""

    api_url = (
        f"https://api.github.com/repos/{owner}/{repository}"
        f"/zipball/{commit}"
    )

    try:
        # GitHub responds with the address of its archive download server.
        with requests.get(
            api_url,
            headers={"User-Agent": "issue-investigator"},
            timeout=30,
            allow_redirects=False,
        ) as response:
            if response.status_code != 302:
                raise ValueError(
                    f"GitHub could not prepare the archive "
                    f"(HTTP {response.status_code})."
                )

            location = response.headers.get("Location", "")

        address = urlsplit(location)

        # Only follow the redirect to GitHub's archive server.
        if (
            address.scheme != "https"
            or address.netloc.lower() != "codeload.github.com"
        ):
            raise ValueError("GitHub returned an unexpected download address.")

        archive = io.BytesIO()

        with requests.get(
            location,
            timeout=30,
            stream=True,
            allow_redirects=False,
        ) as response:
            if response.status_code != 200:
                raise ValueError(
                    f"Archive download failed (HTTP {response.status_code})."
                )

            for chunk in response.iter_content(chunk_size=65_536):
                if archive.tell() + len(chunk) > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Repository download exceeds 20 MB.")

                archive.write(chunk)

    except requests.exceptions.RequestException as error:
        raise ValueError("The GitHub download failed. Try again later.") from error

    archive.seek(0)
    return archive


def extract_python_files(archive, destination):
    """Copy permitted Python files out of the archive."""

    destination = Path(destination).resolve()
    file_count = 0
    source_bytes = 0
    seen_paths = set()

    with zipfile.ZipFile(archive) as zipped:
        entries = zipped.infolist()

        if len(entries) > MAX_ARCHIVE_ENTRIES:
            raise ValueError("The repository contains too many archive entries.")

        for entry in entries:
            archive_path = PurePosixPath(entry.filename)

            if (
                archive_path.is_absolute()
                or ".." in archive_path.parts
                or "\\" in entry.filename
            ):
                raise ValueError("The archive contains an unsafe path.")

            # GitHub wraps the repository contents in one outer folder.
            if entry.is_dir() or len(archive_path.parts) < 2:
                continue

            relative = PurePosixPath(*archive_path.parts[1:])

            if any(
                part.startswith(".") or part in EXCLUDED_FOLDERS
                for part in relative.parts
            ):
                continue

            if relative.suffix != ".py":
                continue

            # Do not recreate links or special filesystem entries.
            mode = entry.external_attr >> 16
            file_type = stat.S_IFMT(mode)

            if file_type not in (0, stat.S_IFREG):
                continue

            if entry.file_size > MAX_FILE_BYTES:
                raise ValueError(
                    f"Python file exceeds 100 KB: {relative}"
                )

            file_count += 1
            source_bytes += entry.file_size

            if file_count > MAX_PYTHON_FILES:
                raise ValueError("Repository exceeds the 200 Python file limit.")

            if source_bytes > MAX_SOURCE_BYTES:
                raise ValueError("Python source exceeds the 5 MB total limit.")

            target = destination.joinpath(*relative.parts).resolve()

            if not target.is_relative_to(destination):
                raise ValueError("An archive path leaves the project folder.")

            # Reject duplicate paths instead of overwriting earlier files.
            if target in seen_paths:
                raise ValueError("The archive contains duplicate file paths.")

            seen_paths.add(target)

            with zipped.open(entry) as source:
                contents = source.read(MAX_FILE_BYTES + 1)

            if len(contents) > MAX_FILE_BYTES:
                raise ValueError(f"Python file exceeds 100 KB: {relative}")

            target.parent.mkdir(parents=True, exist_ok=True)

            with target.open("xb") as output:
                output.write(contents)

    if file_count == 0:
        raise ValueError("No supported Python files were found.")


@contextmanager
def downloaded_repository(url):
    """Provide a temporary project folder and its commit identifier."""

    owner, repository, _ = parse_github_url(url)

    metadata = github_get_json(f"repos/{owner}/{repository}")
    branch = metadata.get("default_branch")

    if not isinstance(branch, str) or not branch:
        raise ValueError("The repository has no default branch.")

    commit_data = github_get_json(
        f"repos/{owner}/{repository}/commits/{quote(branch, safe='')}"
    )
    commit = commit_data.get("sha")

    if not isinstance(commit, str) or not re.fullmatch(
        r"[0-9a-fA-F]{40}", commit
    ):
        raise ValueError("GitHub returned an invalid commit identifier.")

    archive = download_archive(owner, repository, commit)

    # This directory is removed when the with block finishes.
    with archive, tempfile.TemporaryDirectory(
        prefix="issue-investigator-"
    ) as temporary_folder:
        project_folder = Path(temporary_folder)

        try:
            extract_python_files(archive, project_folder)
        except (zipfile.BadZipFile, OSError, RuntimeError) as error:
            raise ValueError("Could not extract the repository archive.") from error

        yield project_folder, commit