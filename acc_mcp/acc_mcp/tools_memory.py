import httpx
from mcp import types as mcp_types

MEMORY_BASE_URL = "http://localhost:8001"  # where acc_memory/api.py runs

async def memory_save_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    container = args.arguments["container_key"]
    facts = args.arguments["facts"]
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{MEMORY_BASE_URL}/memory/save",
            params={"container_key": container},
            json=facts,
        )
        r.raise_for_status()
    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text="saved")]
    )

async def memory_search_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    container = args.arguments["container_key"]
    query = args.arguments["query"]
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{MEMORY_BASE_URL}/memory/search",
            params={"container_key": container, "query": query},
        )
        r.raise_for_status()
        items = r.json()
    # naive formatting for now
    lines = [f"{i['kind']}: {i['subject']} {i['predicate']} {i['object']}" for i in items]
    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text="\n".join(lines))]
    )
