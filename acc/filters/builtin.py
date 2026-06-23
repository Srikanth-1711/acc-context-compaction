BUILTIN_FILTERS = {
    "git status": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(On branch|Your branch is up to date|nothing to commit|no changes added to commit|Changes not staged for commit:)"},
            {"name": "regex_keep", "pattern": "(modified|deleted|new file|renamed|Untracked files|error|fatal)"},
            {"name": "smart_truncate", "max_lines": 20, "head_ratio": 0.5},
            {"name": "on_empty", "fallback": "[git status: clean]"}
        ]
    },
    "git log": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "smart_truncate", "max_lines": 50, "head_ratio": 1.0}
        ]
    },
    "git diff": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^index "},
            {"name": "smart_truncate", "max_lines": 100, "head_ratio": 0.5, "priority_lines": "^@@"}
        ]
    },
    "cargo build": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(Compiling|Finished|Running|Updating|Downloading|Documenting|Blocking|Unblocking)"},
            {"name": "regex_keep", "pattern": "(error|warning|FAILED|test result|panicked)"},
            {"name": "smart_truncate", "max_lines": 30, "head_ratio": 0.3}
        ]
    },
    "cargo test": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(Compiling|Finished|Running|Updating|Downloading|Documenting)"},
            {"name": "regex_keep", "pattern": "(test result:|FAILED|error|warning|panicked)"},
            {"name": "smart_truncate", "max_lines": 50, "head_ratio": 0.3, "priority_lines": "(test result:|FAILED)"},
            {"name": "on_empty", "fallback": "[cargo test: all passed]"}
        ]
    },
    "pytest": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(platform|rootdir:|collected |plugins:)"},
            {"name": "regex_keep", "pattern": "(FAILED|ERROR|Exception|Traceback|==.*passed.*==)"},
            {"name": "smart_truncate", "max_lines": 50, "head_ratio": 0.2, "priority_lines": "(FAILED|ERROR)"},
            {"name": "on_empty", "fallback": "[pytest: all passed]"}
        ]
    },
    "python -m pytest": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(platform|rootdir:|collected |plugins:)"},
            {"name": "regex_keep", "pattern": "(FAILED|ERROR|Exception|Traceback|==.*passed.*==)"},
            {"name": "smart_truncate", "max_lines": 50, "head_ratio": 0.2, "priority_lines": "(FAILED|ERROR)"},
            {"name": "on_empty", "fallback": "[pytest: all passed]"}
        ]
    },
    "npm test": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "regex_drop", "pattern": "^(> |PASS |Test Suites:|Tests:|Snapshots:|Time:)"},
            {"name": "regex_keep", "pattern": "(FAIL|error|failed|Error:)"},
            {"name": "smart_truncate", "max_lines": 50, "head_ratio": 0.2, "priority_lines": "FAIL"},
            {"name": "on_empty", "fallback": "[npm test: all passed]"}
        ]
    },
    "ls -la": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "smart_truncate", "max_lines": 100, "head_ratio": 0.5}
        ]
    },
    "tree": {
        "stages": [
            {"name": "strip_ansi"},
            {"name": "smart_truncate", "max_lines": 100, "head_ratio": 0.5}
        ]
    }
}
