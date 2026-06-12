from typing import List, Dict

def format_pytest(parsed: Dict, raw_lines: List[str]) -> str:
    lines = []
    if parsed.get("summary"):
        lines.append(f"PYTEST SUMMARY: {parsed['summary']}")
    if parsed["failures"]:
        lines.append("FAILING TESTS:")
        for f in parsed["failures"][:20]:
            lines.append(f"- {f['file']}:: {f['test']} — {f['reason']}")
    else:
        lines.append("No explicit failing tests detected in parsed output.")
    return "\n".join(lines)

def format_git_status(parsed: Dict, raw_lines: List[str]) -> str:
    lines = ["GIT STATUS SUMMARY:"]
    if parsed["modified"]:
        lines.append("Modified Files:")
        lines.extend([f"  {f}" for f in parsed["modified"][:20]])
    if parsed["untracked"]:
        lines.append("Untracked Files:")
        lines.extend([f"  {f}" for f in parsed["untracked"][:20]])
    if not parsed["modified"] and not parsed["untracked"]:
        lines.append("Working tree clean.")
    return "\n".join(lines)

def format_git_log(parsed: Dict, raw_lines: List[str]) -> str:
    lines = ["GIT LOG SUMMARY:"]
    for c in parsed["commits"][:20]:
        lines.append(f"- {c['hash']} {c['message']}")
    return "\n".join(lines)

def format_git_diff(parsed: Dict, raw_lines: List[str]) -> str:
    lines = ["GIT DIFF SUMMARY:"]
    if parsed["files_changed"]:
        lines.append("Files Changed:")
        for f in parsed["files_changed"][:10]:
            lines.append(f"  {f.replace('diff --git a/', '').replace(' b/', ' -> ')}")
    if parsed["hunks"]:
        lines.append("Hunks modified:")
        for h in parsed["hunks"][:10]:
            lines.append(f"  {h}")
    return "\n".join(lines)
