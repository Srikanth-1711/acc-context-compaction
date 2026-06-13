from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager
from acc.compaction.parsers import get_parser
from acc.compaction.dedup_cache import get_session_cache
from mcp import types as mcp_types

async def compress_context_tool(args: dict) -> list:
    text = args.get("text", "")
    profile_name = args.get("profile")
    command = args.get("command")
    verbosity = args.get("verbosity", "compact")
    
    # Check dedup cache before expensive processing
    cache = get_session_cache()
    cache.next_turn()
    suppressed = cache.check(text)
    if suppressed:
        return [mcp_types.TextContent(type="text", text=suppressed)]
    
    # Try structured parsing if command hint is provided
    if command:
        parser = get_parser(command)
        if parser:
            try:
                # Some parsers accept kwargs like verbosity
                text = parser.parse(text, verbosity=verbosity)
            except TypeError:
                try:
                    text = parser.parse(text)
                except Exception:
                    pass
            except Exception:
                pass  # Fall through to generic pipeline
    
    pm = ProfileManager()
    profile = {}
    if profile_name:
        profile = pm.load_profile(profile_name)
        
    pipeline = FilterPipeline(profile)
    compressed = pipeline.execute(text)
    
    return [mcp_types.TextContent(type="text", text=compressed)]

