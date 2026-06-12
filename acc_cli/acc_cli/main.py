import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

import typer

from .config import load_config
from .filters import filter_noise, dedup, truncate
from .parsers import parse_pytest, parse_git_status, parse_git_log, parse_git_diff
from .formatter import format_pytest, format_git_status, format_git_log, format_git_diff

app = typer.Typer(help="ACC CLI: compact command output for AI agents")

def run_command(cmd: List[str], cwd: Path | None = None) -> List[str]:
    cmd = list(cmd)
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
    lines: List[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        lines.append(line)
    proc.wait()
    return lines

@app.command()
def run(
    cmd: List[str] = typer.Argument(..., help="Command to run, e.g. 'pytest -q'"),
    cwd: str = typer.Option(".", help="Working directory"),
    hint: str = typer.Option("", help="Optional hint about what you care about"),
):
    """
    Run an arbitrary command and print compacted output.
    """
    config = load_config()
    raw = run_command(cmd, Path(cwd))
    filtered = filter_noise(raw)
    deduped = dedup(filtered, window=config.dedup_window)
    compact = truncate(deduped, max_lines=config.max_lines, raw_lines=raw)

    # simple command-specific routing for demo
    joined_cmd = " ".join(cmd)
    if joined_cmd.startswith("pytest"):
        parsed = parse_pytest(compact)
        out = format_pytest(parsed, compact)
    elif joined_cmd.startswith("git status"):
        parsed = parse_git_status(compact)
        out = format_git_status(parsed, compact)
    elif joined_cmd.startswith("git log"):
        parsed = parse_git_log(compact)
        out = format_git_log(parsed, compact)
    elif joined_cmd.startswith("git diff"):
        parsed = parse_git_diff(compact)
        out = format_git_diff(parsed, compact)
    else:
        out = "\n".join(compact)

    print(out)

if __name__ == "__main__":
    app()
