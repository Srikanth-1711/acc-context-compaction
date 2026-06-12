from mcp import types as mcp_types
from acc.repo.compressor import compress_repository

async def compress_repository_tool(args: dict) -> list:
    directory = args.get("directory", ".")
    compressed = compress_repository(directory)
    
    return [mcp_types.TextContent(type="text", text=compressed)]
