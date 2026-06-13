import os
from pathlib import Path
from acc.repo.analyzer import build_import_graph
from acc.repo.ranker import rank_files
from acc.structured.python_ast import compress_python

def compress_repository(directory: str) -> str:
    """
    Scans a directory, builds a dependency graph, ranks files, and applies
    selective compression based on their rank.
    """
    root_path = Path(directory).resolve()
    if not root_path.exists() or not root_path.is_dir():
        return f"Error: Directory {directory} not found."
        
    graph = build_import_graph(str(root_path))
    if not graph:
        return "No python files found or unable to parse repository."
        
    ranked = rank_files(graph)
    total_files = len(ranked)
    
    core_cutoff = max(1, int(total_files * 0.05))
    peripheral_cutoff = max(1, int(total_files * 0.30))
    
    core_files = {r[0] for r in ranked[:core_cutoff]}
    peripheral_files = {r[0] for r in ranked[core_cutoff:peripheral_cutoff]}
    # The rest are leaf files
    
    output = []
    output.append(f"=== Repository Architecture ({total_files} files) ===")
    
    for module_name, score in ranked:
        # Convert module name back to path
        parts = module_name.split(".")
        if os.path.exists(root_path / Path(*parts).with_suffix(".py")):
            file_path = root_path / Path(*parts).with_suffix(".py")
        elif os.path.exists(root_path / Path(*parts) / "__init__.py"):
            file_path = root_path / Path(*parts) / "__init__.py"
        else:
            continue
            
        output.append(f"\n--- File: {file_path.relative_to(root_path)} (Rank Score: {score}) ---")
        
        if module_name in core_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                # Core: Skeletonize (remove bodies), but keep docstrings
                compressed = compress_python(code, skeletonize=True, strip_docstrings=False)
                output.append(compressed)
            except Exception:
                continue
        elif module_name in peripheral_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                # Peripheral: Skeletonize AND strip docstrings
                compressed = compress_python(code, skeletonize=True, strip_docstrings=True)
                output.append(compressed)
            except Exception:
                continue
        else:
            # Leaf: Extreme compression (Path only, zero AST parsing)
            # We already printed the filename above. Do not read or append the code.
            pass
                
    return "\n".join(output)
