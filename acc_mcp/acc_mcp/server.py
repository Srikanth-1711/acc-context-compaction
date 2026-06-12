from mcp.server import Server
from mcp import types as mcp_types

from .tools_cli import cli_run_tool
from .tools_memory import memory_save_tool, memory_search_tool

server = Server("acc")

@server.tool(
    name="cli_run",
    description="Run a shell command and return compacted output suitable for LLMs",
    input_schema={
        "type": "object",
        "properties": {
            "cmd": {"type": "array", "items": {"type": "string"}},
            "cwd": {"type": "string"},
            "hint": {"type": "string"},
        },
        "required": ["cmd"],
    },
)
async def cli_run(input: mcp_types.ToolInput) -> mcp_types.ToolResult:
    return await cli_run_tool(input)

@server.tool(
    name="memory_save",
    description="Save durable facts about a project/service/user for future recall",
    input_schema={
        "type": "object",
        "properties": {
            "container_key": {"type": "string"},
            "facts": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["container_key", "facts"],
    },
)
async def memory_save(input: mcp_types.ToolInput) -> mcp_types.ToolResult:
    return await memory_save_tool(input)

@server.tool(
    name="memory_search",
    description="Search for previously stored facts for a given container",
    input_schema={
        "type": "object",
        "properties": {
            "container_key": {"type": "string"},
            "query": {"type": "string"},
        },
        "required": ["container_key", "query"],
    },
)
async def memory_search(input: mcp_types.ToolInput) -> mcp_types.ToolResult:
    return await memory_search_tool(input)

def main():
    from mcp.server.stdio import stdio_server
    stdio_server(server)

if __name__ == "__main__":
    main()
