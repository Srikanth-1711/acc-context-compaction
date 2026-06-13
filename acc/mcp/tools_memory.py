from mcp import types as mcp_types

from acc.services.memory_service import save_memory, search_memory
from acc.schemas.memory import MemoryCreate, MemorySearch, Fact

async def memory_save_tool(args: dict) -> list:
    container_key = args["container_key"]
    facts_raw = args["facts"]
    
    facts = []
    for f in facts_raw:
        facts.append(Fact(
            subject=f.get("subject", ""),
            predicate=f.get("predicate", ""),
            object=f.get("object", ""),
            scope=f.get("scope", "")
        ))
        
    memory_in = MemoryCreate(container_key=container_key, facts=facts)
    save_memory(memory_in)
    
    return [mcp_types.TextContent(type="text", text=f"Saved {len(facts)} facts to memory.")]

async def memory_search_tool(args: dict) -> list:
    container_key = args["container_key"]
    query = args["query"]
    
    req = MemorySearch(container_key=container_key, query=query)
    results = search_memory(req)
    
    import json
    return mcp_types.ToolResult(
        content=[mcp_types.TextContent(text=json.dumps(results, indent=2))]
    )
