from pathlib import Path
from typing import List

from mcp import types as mcp_types
from acc.services.compaction_service import run_compaction

async def cli_run_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    cmd: List[str] = args.arguments["cmd"]
    cwd = Path(args.arguments.get("cwd", "."))
    
    text = run_compaction(cmd, cwd)

    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text=text)]
    )
