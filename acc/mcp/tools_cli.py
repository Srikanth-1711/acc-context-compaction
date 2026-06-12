from pathlib import Path
from typing import List

from acc.services.compaction_service import run_compaction
from mcp import types as mcp_types

async def cli_run_tool(args: dict) -> list:
    cmd: List[str] = args.get("cmd", [])
    cwd = Path(args.get("cwd", "."))
    
    text = run_compaction(cmd, cwd)

    return [mcp_types.TextContent(type="text", text=text)]
