from typing import Dict, List, Tuple

def rank_files(import_graph: Dict[str, List[str]]) -> List[Tuple[str, int]]:
    """
    Calculates the in-degree (importance) of each file in the repository.
    Returns a list of (module_name, score) sorted by score descending.
    """
    # Initialize scores
    scores = {module: 0 for module in import_graph.keys()}
    
    # Calculate in-degree (how many times a module is imported by others IN the repo)
    for module, imports in import_graph.items():
        for imp in imports:
            # We only care about internal repository dependencies
            # We can do a naive prefix match to see if the import is internal
            for known_module in scores.keys():
                if imp == known_module or imp.startswith(known_module + "."):
                    scores[known_module] += 1
                    break
                    
    # Sort descending by score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores
