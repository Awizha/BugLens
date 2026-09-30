from tools import read_code, list_python_files, search_code


def get_issue():
    issue = input("Describe the bug: ").strip()
    return issue


issue = get_issue()

if not issue:
    print("Please enter a bug description.")
else:
    print("\nBug report received:")
    print(issue)
    files = list_python_files("sample_project")

    for file in files:
        print(f"\nCode in {file}:")
        print(read_code(file))

    keyword = input("\nSearch keyword: ").strip()

    if not keyword:
        print("Please enter a search keyword.")
    else:
        results = search_code("sample_project", keyword)

        if not results:
            print(f"No matches found for: {keyword}")
        else:
            print("\nSearch results:")
            for result in results:
                print(result)