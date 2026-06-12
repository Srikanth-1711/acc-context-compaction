import re
from typing import List, Dict

PYTEST_FAIL_RE = re.compile(r"^FAILED\s+(.+?)::(.+?)\s+\[([^\]]+)\]")

def parse_pytest(lines: List[str]) -> Dict:
    failures = []
    summary_line = None
    for line in lines:
        if " failed," in line and " passed" in line:
            summary_line = line.strip()
        m = PYTEST_FAIL_RE.match(line)
        if m:
            file_path, test_name, reason = m.groups()
            failures.append({
                "file": file_path,
                "test": test_name,
                "reason": reason,
            })
    return {"summary": summary_line, "failures": failures}

def parse_git_status(lines: List[str]) -> Dict:
    # A simple parser for git status -s
    modified = []
    untracked = []
    for line in lines:
        if len(line) < 3: continue
        status = line[:2]
        file_path = line[3:].strip()
        if "??" in status:
            untracked.append(file_path)
        else:
            modified.append(f"{status.strip()} {file_path}")
    return {"modified": modified, "untracked": untracked}

def parse_git_log(lines: List[str]) -> Dict:
    commits = []
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2 and len(parts[0]) >= 7:
            commits.append({"hash": parts[0], "message": parts[1].strip()})
    return {"commits": commits}

def parse_git_diff(lines: List[str]) -> Dict:
    # Extract just the files that changed and the hunk headers
    files_changed = []
    hunks = []
    for line in lines:
        if line.startswith("diff --git"):
            files_changed.append(line.strip())
        elif line.startswith("@@ "):
            hunks.append(line.strip())
    return {"files_changed": files_changed, "hunks": hunks}
