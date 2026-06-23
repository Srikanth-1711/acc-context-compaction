import os
from pathlib import Path
from acc.repo.symbol_graph import build_symbol_graph
from acc.repo.pagerank import pagerank
from acc.repo.budget import select_within_budget

def compress_repository(directory: str, token_limit: int = 50000, active_files: list[str] = None) -> str:
    """
    Scans a directory, builds a SymbolGraph, ranks functions via PageRank, and packs
    the context window up to the token_limit.
    """
    root_path = Path(directory).resolve()
    if not root_path.exists() or not root_path.is_dir():
        return f"Error: Directory {directory} not found."
        
    try:
        graph = build_symbol_graph(str(root_path))
    except Exception as e:
        return f"Error building symbol graph: {e}"
        
    if not graph.nodes:
        return "No supported source files found or unable to parse repository."
        
    ranked = pagerank(graph, active_files=set(active_files) if active_files else None)
    
    # Greedily pack the tokens
    output = select_within_budget(ranked, token_limit)
    
    return output
