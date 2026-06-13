import asyncio
from mcp.server import Server
from mcp import types as mcp_types

from acc.mcp.tools_cli import cli_run_tool
from acc.mcp.tools_memory import memory_save_tool, memory_search_tool
from acc.mcp.tools_compaction import compress_context_tool
from acc.mcp.tools_repo import compress_repository_tool

server = Server("acc")

@server.list_tools()
async def handle_list_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="cli_run",
            description="Run a shell command and return compacted output suitable for LLMs",
            inputSchema={
                "type": "object",
                "properties": {
                    "cmd": {"type": "array", "items": {"type": "string"}},
                    "cwd": {"type": "string"},
                    "hint": {"type": "string"},
                },
                "required": ["cmd"],
            }
        ),
        mcp_types.Tool(
            name="compress_context",
            description="Compress raw text or code structurally to save LLM tokens",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "profile": {"type": "string", "description": "Optional profile name like 'python_code', 'pytest', 'docker'"},
                    "verbosity": {"type": "string", "description": "Optional. Set to 'full' to disable aggressive truncation.", "enum": ["compact", "full"]}
                },
                "required": ["text"],
            }
        ),
        mcp_types.Tool(
            name="slice_file",
            description="Return a structural index of a source file (imports, classes, functions) with optional focused function body",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "focus_function": {"type": "string", "description": "Function name to include full body for"},
                },
                "required": ["file_path"],
            }
        ),
        mcp_types.Tool(
            name="compress_repository",
            description="Scan a codebase directory, map its architecture, and return a structurally compressed representation",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Absolute or relative path to the repository directory"},
                },
                "required": ["directory"],
            }
        ),
        mcp_types.Tool(
            name="memory_save",
            description="Save durable facts about a project/service/user for future recall",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_key": {"type": "string"},
                    "facts": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["container_key", "facts"],
            }
        ),
        mcp_types.Tool(
            name="memory_search",
            description="Search for previously stored facts for a given container",
            inputSchema={
                "type": "object",
                "properties": {
                    "container_key": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["container_key", "query"],
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
    if not arguments:
        arguments = {}
        
    if name == "cli_run":
        return await cli_run_tool(arguments)
    elif name == "compress_context":
        return await compress_context_tool(arguments)
    elif name == "slice_file":
        from acc.compaction.slicer import slice_file
        result = slice_file(arguments["file_path"], arguments.get("focus_function"))
        return [mcp_types.TextContent(type="text", text=result)]
    elif name == "compress_repository":
        return await compress_repository_tool(arguments)
    elif name == "memory_save":
        return await memory_save_tool(arguments)
    elif name == "memory_search":
        return await memory_search_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

def run():
    from mcp.server.stdio import stdio_server
    
    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
            
    asyncio.run(_run())

if __name__ == "__main__":
    run()
