from mcp import types as mcp_types

from acc.services.memory_service import save_memory, search_memory
from acc.schemas.memory import MemoryCreate, MemorySearch, Fact

async def memory_save_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    container_key = args.arguments["container_key"]
    facts_raw = args.arguments["facts"]
    
    facts = []
    for f in facts_raw:
        facts.append(Fact(
            subject=f.get("subject", ""),
            predicate=f.get("predicate", ""),
            object=f.get("object", ""),
            scope=f.get("scope", "")
        ))
        
    req = MemoryCreate(container_key=container_key, facts=facts)
    save_memory(req)
    
    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text="Facts saved successfully.")]
    )

async def memory_search_tool(args: mcp_types.ToolInput) -> mcp_types.ToolResult:
    container_key = args.arguments["container_key"]
    query = args.arguments["query"]
    
    req = MemorySearch(container_key=container_key, query=query)
    results = search_memory(req)
    
    import json
    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text=json.dumps(results, indent=2))]
    )
