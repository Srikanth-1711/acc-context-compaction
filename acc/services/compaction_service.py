import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

from acc.core.config import settings
from acc.core.logger import log
from acc.filters.reduction import filter_noise, dedup, truncate
from acc.compaction.parsers import parse_pytest, parse_git_status, parse_git_log, parse_git_diff
from acc.compaction.formatter import format_pytest, format_git_status, format_git_log, format_git_diff

def run_compaction(cmd: List[str], cwd: Path | None = None) -> str:
    log.info("Running compaction service", extra={"cmd": cmd, "cwd": str(cwd)})
    if len(cmd) == 1 and " " in cmd[0]:
        cmd = cmd[0].split(" ")
        
    if sys.platform == "win32":
        resolved = shutil.which(cmd[0])
        if resolved:
            cmd[0] = resolved
            
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []
    assert proc.stdout is not None
    for line in proc.stdout:
        raw.append(line)
    proc.wait()

    filtered = filter_noise(raw)
    deduped = dedup(filtered, window=settings.dedup_window)
    compact = truncate(deduped, max_lines=settings.max_lines, raw_lines=raw)

    joined_cmd = " ".join(cmd)
    if joined_cmd.startswith("pytest"):
        parsed = parse_pytest(compact)
        text = format_pytest(parsed, compact)
    elif joined_cmd.startswith("git status"):
        parsed = parse_git_status(compact)
        text = format_git_status(parsed, compact)
    elif joined_cmd.startswith("git log"):
        parsed = parse_git_log(compact)
        text = format_git_log(parsed, compact)
    elif joined_cmd.startswith("git diff"):
        parsed = parse_git_diff(compact)
        text = format_git_diff(parsed, compact)
    else:
        text = "\n".join(compact)

    return text
