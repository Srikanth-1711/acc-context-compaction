from mcp.server.fastmcp import FastMCP
from pydantic import Field
from typing import List, Optional

from acc.compaction.pipeline import FilterPipeline
from acc.compaction.dedup import get_session_cache
from acc.memory.retrieval import MemoryRetriever
from acc.compression.deterministic import DeterministicCompressor
from acc.compaction.executor import execute_command
from acc.telemetry.tracker import AnalyticsTracker
from sqlmodel import Session
import tiktoken
import logging

# Create FastMCP server
mcp = FastMCP("acc")

# Get analytics engine for the MCP session
tracker = AnalyticsTracker()

try:
    _encoder = tiktoken.get_encoding("cl100k_base")
except Exception as e:
    logging.warning(f"Failed to load tiktoken encoding: {e}")
    _encoder = None

def count_tokens(text: str) -> int:
    """Token counter using tiktoken with fallback"""
    if not text:
        return 0
    if _encoder:
        try:
            return len(_encoder.encode(text))
        except Exception as e:
            logging.warning(f"tiktoken failed, using fallback: {e}")
    return len(text) // 4

@mcp.tool()
def acc_run(
    command: str,
    args: Optional[List[str]] = None,
    context: Optional[dict] = None,
    session_id: Optional[str] = None
) -> dict:
    """
    The unified context optimizer for running shell commands.
    """
    if session_id is None:
        session_id = context.get("session_id", "default") if context else "default"
        
    cache = get_session_cache(session_id)
    cache.next_turn()
    
    cmd_list = [command] + (args or [])
    
    # 1. MEMORY LAYER: Retrieve relevant facts BEFORE running command
    memories = []
    if context and "current_file" in context:
        with Session(tracker.engine) as session:
            retriever = MemoryRetriever(session)
            memories = retriever.temporal_query(
                subject=context["current_file"]
            )
    
    # 2. EXECUTION: Run the command safely
    exec_result = execute_command(cmd_list)
    raw_output = exec_result.stdout
    if exec_result.error:
        raw_output += f"\n{exec_result.error}"
    
    # 3. DEDUP: Check if we've seen this exact output before
    dedup_result = cache.check(raw_output)
    if dedup_result:
        tracker.log_run(
            command=command,
            raw_tokens=count_tokens(raw_output),
            output_tokens=count_tokens(dedup_result),
            deduped=True,
            memories_used=len(memories)
        )
        return {
            "output": dedup_result,
            "tokens_saved": count_tokens(raw_output),
            "deduped": True,
            "memories_injected": len(memories),
            "compression_ratio": 0.01
        }
    
    # 4. FILTER: Apply command-specific + TOML filters
    pipeline = FilterPipeline.for_command(command)
    filtered = pipeline.run(raw_output)
    
    # 5. COMPRESS: Deterministic fallback
    compressor = DeterministicCompressor()
    compressed = compressor.run(filtered)
    
    # 6. TRACK: Log savings
    tracker.log_run(
        command=command,
        raw_tokens=count_tokens(raw_output),
        output_tokens=count_tokens(compressed),
        memories_used=len(memories)
    )
    
    # 7. RETURN: Structured response
    return {
        "output": compressed,
        "tokens_saved": max(0, count_tokens(raw_output) - count_tokens(compressed)),
        "deduped": False,
        "memories_injected": len(memories),
        "compression_ratio": count_tokens(compressed) / count_tokens(raw_output) if count_tokens(raw_output) > 0 else 1.0,
        "truncated": pipeline.was_truncated,
        "full_output_path": pipeline.tee_path if pipeline.was_truncated else None
    }

@mcp.tool()
def acc_remember(facts: List[dict]) -> dict:
    """
    Save facts into the temporal memory layer.
    """
    saved_count = 0
    with Session(tracker.engine) as session:
        retriever = MemoryRetriever(session)
        for fact in facts:
            retriever.save_fact(
                subject=fact.get("subject", "unknown"),
                predicate=fact.get("predicate", "is"),
                object_value=fact.get("object_value", ""),
                scope=fact.get("scope", "global"),
                kind=fact.get("kind", "fact")
            )
            saved_count += 1
    return {"status": "success", "saved": saved_count}

@mcp.tool()
def acc_search(query: str, search_type: str = "keyword") -> str:
    """
    Search temporal memory.
    """
    with Session(tracker.engine) as session:
        retriever = MemoryRetriever(session)
        if search_type == "temporal":
            results = retriever.temporal_query(query)
            return "\n".join([f"- {r.subject} {r.predicate} {r.object}" for r in results])
        else:
            results = retriever.keyword_search(query)
            return "\n".join([f"- {r[0].subject} {r[0].predicate} {r[0].object} (score: {r[1]:.2f})" for r in results])

@mcp.resource("acc://analytics")
def get_analytics() -> str:
    """Returns markdown summary of token savings."""
    return tracker.get_markdown_report()

@mcp.resource("acc://analytics/{period}")
def get_period_analytics(period: str) -> dict:
    """Returns JSON analytics for period: day, week, month, or all."""
    return tracker.get_json(period)

@mcp.resource("acc://status")
def get_status() -> dict:
    """Health check for ACC MCP server."""
    return {
        "status": "healthy",
        "telemetry_db": str(tracker.engine.url)
    }

def main():
    mcp.run()

if __name__ == "__main__":
    main()
