from agent import investigate_issue


issue = input("Describe the bug: ").strip()

findings = investigate_issue(
    issue,
    on_progress=print,
)

print("\nFindings:")
print(findings)