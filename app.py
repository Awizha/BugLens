import os

import streamlit as st

from agent import investigate_issue
from github_source import parse_github_url, read_github_issue
from repository_download import downloaded_repository


st.set_page_config(
    page_title="Issue Investigator",
    page_icon="🔎",
    layout="centered",
)

st.title("Issue Investigator")
st.write(
    "Investigate a bug in a public Python repository "
    "using source-code evidence."
)

st.caption(
    "Inspected source code and your bug report are sent to OpenRouter "
    "and its selected model provider. Suggested fixes are not applied "
    "or tested automatically."
)

# Collect inputs together when the button is clicked.
with st.form("investigation_form"):
    github_url = st.text_input(
        "GitHub repository or issue URL",
        placeholder="https://github.com/owner/repository",
    )

    bug_description = st.text_area(
        "Describe the bug",
        placeholder="What happened, and what should have happened?",
        help=(
            "Required for a repository URL. For an issue URL, "
            "we import the issue and add any details you write here."
        ),
        height=140,
        max_chars=20_000,
    )

    submitted = st.form_submit_button(
        "Investigate",
        type="primary",
    )


if submitted:
    # Check the inputs before making network requests.
    try:
        owner, repository, issue_number = parse_github_url(github_url)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    if issue_number is None and not bug_description.strip():
        st.error("Enter a bug description for this repository.")
        st.stop()

    if not os.getenv("OPENROUTER_API_KEY"):
        st.error("Add OPENROUTER_API_KEY to your .env file first.")
        st.stop()

    progress = st.status(
        "Preparing investigation...",
        expanded=True,
    )

    try:
        issue = bug_description.strip()

        if issue_number is not None:
            progress.write("Reading the GitHub issue...")
            imported_issue = read_github_issue(github_url)

            if issue:
                issue = (
                    f"{imported_issue}\n\n"
                    f"Additional details from the user:\n{issue}"
                )
            else:
                issue = imported_issue

        if len(issue) > 20_000:
            raise ValueError(
                "The combined bug report is too long. "
                "Use a repository URL with a shorter description."
            )

        progress.write("Downloading the repository...")

        # The downloaded files exist until this block finishes.
        with downloaded_repository(github_url) as (folder, commit):
            progress.write(f"Repository: {owner}/{repository}")
            progress.write(f"Commit: {commit}")
            progress.write("Inspecting code...")

            # Display a progress message without returning a value.
            def show_progress(message: str) -> None:
                progress.text(message)

            findings = investigate_issue(
                issue,
                on_progress=show_progress,
                project_folder=folder,
            )

        progress.write("Temporary download removed.")
        progress.update(
            label="Run ended — review the result below.",
            state="complete",
            expanded=False,
        )

    except (ValueError, OSError) as error:
        progress.update(
            label="Could not finish the run.",
            state="error",
        )
        st.error(str(error))
        st.stop()

    st.subheader("Result")
    st.caption(f"Inspected commit: {commit}")
    st.markdown(findings)

    with st.expander("Bug report used"):
        st.text(issue)