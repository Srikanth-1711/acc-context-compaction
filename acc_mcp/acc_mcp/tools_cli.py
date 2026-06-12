import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

from mcp import types as mcp_types

from acc_cli.filters import filter_noise, dedup, truncate
from acc_cli.parsers import parse_pytest, parse_git_status, parse_git_log, parse_git_diff
from acc_cli.formatter import format_pytest, format_git_status, format_git_log, format_git_diff
from acc_cli.config import load_config

async def cli_run_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    cmd: List[str] = args.arguments["cmd"]
    cwd = Path(args.arguments.get("cwd", "."))
    hint = args.arguments.get("hint", "")

    config = load_config()
    
    if len(cmd) == 1 and " " in cmd[0]:
        cmd = cmd[0].split(" ")
        
    if sys.platform == "win32":
        resolved = shutil.which(cmd[0])
        if resolved:
            cmd[0] = resolved
            
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
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
    deduped = dedup(filtered, window=config.dedup_window)
    compact = truncate(deduped, config.max_lines, raw_lines=raw)

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

    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text=text)]
    )
