from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager
from mcp import types as mcp_types

async def compress_context_tool(args: dict) -> list:
    text = args.get("text", "")
    profile_name = args.get("profile")
    
    pm = ProfileManager()
    profile = {}
    if profile_name:
        profile = pm.load_profile(profile_name)
        
    pipeline = FilterPipeline(profile)
    compressed = pipeline.execute(text)
    
    return [mcp_types.TextContent(type="text", text=compressed)]
