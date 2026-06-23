from typing import List, Tuple, Set
import os

from acc.repo.symbol_graph import Node
from acc.evals.harness import count_tokens
from acc.compaction.slicer import slice_file

def select_within_budget(
    ranked_symbols: List[Tuple[Node, float]], 
    token_limit: int
) -> str:
    """
    Greedily packs source files/symbols into the context window until the budget is hit.
    We iterate over the top symbols. If a file isn't included yet, we add its skeleton (slice_file).
    If we have room, we expand the specific top symbols to their full bodies.
    """
    if token_limit <= 0:
        return ""
        
    output_parts = []
    current_tokens = 0
    
    # Track which files we've added skeletons for
    added_files: Set[str] = set()
    # Track which specific functions we've expanded
    expanded_symbols: Set[Node] = set()
    
    for node, score in ranked_symbols:
        if current_tokens >= token_limit:
            break
            
        file_path = node.file_path
        
        if file_path not in added_files:
            # First time seeing this file -> add its skeleton with this function expanded
            try:
                content = slice_file(file_path, focus_function=node.name)
                tokens = count_tokens(content)
                
                if current_tokens + tokens <= token_limit:
                    output_parts.append(content)
                    current_tokens += tokens
                    added_files.add(file_path)
                    expanded_symbols.add(node)
                else:
                    # Try just the skeleton without expanding the function
                    skeleton = slice_file(file_path, focus_function=None)
                    skel_tokens = count_tokens(skeleton)
                    if current_tokens + skel_tokens <= token_limit:
                        output_parts.append(skeleton)
                        current_tokens += skel_tokens
                        added_files.add(file_path)
            except Exception:
                continue
        else:
            # We already have the skeleton for this file. 
            # In a true dynamic system, we'd go back and replace the skeleton with a newly expanded function.
            # For now, if we already included the file, we skip trying to re-expand another function 
            # (slice_file currently only supports one focus_function at a time).
            # A more advanced implementation would edit the existing output_parts entry.
            pass
            
    if not output_parts:
        return "[BUDGET] Token limit too small to include any files."
        
    header = f"=== Context Packed ({current_tokens:,} / {token_limit:,} tokens) ===\n"
    return header + "\n\n".join(output_parts)
