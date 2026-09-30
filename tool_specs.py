TOOL_SPECS = [
    {
        "type": "function",
        "name": "list_python_files",
        "description": "List Python files inside sample_project.",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Use sample_project or a folder inside it.",
                }
            },
            "required": ["folder_path"],
        },
    },
    
    
    
    
    #read code func
    {
        "type": "function",
        "name": "read_code",
        "description": "Read a Python source file with line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to a file inside sample_project.",
                }
            },
            "required": ["file_path"],
        },
    },
    
    
    #search code
    
    {
        "type": "function",
        "name": "search_code",
        "description": "Find lines containing a keyword. Search is case-sensitive.",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Use sample_project or a folder inside it.",
                },
                "keyword": {
                    "type": "string",
                    "description": "Non-empty text to search for.",
                },
            },
            "required": ["folder_path", "keyword"],
        },
    },
]