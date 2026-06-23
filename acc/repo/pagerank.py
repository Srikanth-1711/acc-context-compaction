from typing import List, Tuple, Set
from acc.repo.symbol_graph import SymbolGraph, Node

def pagerank(
    graph: SymbolGraph, 
    active_files: Set[str] = None,
    damping_factor: float = 0.85, 
    max_iter: int = 100, 
    tol: float = 1.0e-6
) -> List[Tuple[Node, float]]:
    """
    Computes Personalized PageRank for the SymbolGraph.
    
    If active_files is provided, nodes belonging to those files receive a higher
    restart probability, biasing the rank towards the user's active context.
    """
    nodes = list(graph.nodes)
    if not nodes:
        return []

    N = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # Calculate out-degrees
    out_degree = {node: len(graph.edges[node]) for node in nodes}
    
    # Build personalization vector
    p = [1.0 / N] * N
    if active_files:
        active_weight = 10.0
        base_weight = 1.0
        total_weight = 0.0
        
        weights = []
        for node in nodes:
            # Check if node.file_path matches any active file (naive substring/endswith match)
            is_active = any(node.file_path.endswith(af) or af in node.file_path for af in active_files)
            w = active_weight if is_active else base_weight
            weights.append(w)
            total_weight += w
            
        p = [w / total_weight for w in weights]
        
    # Initialize PageRank vector
    pr = list(p)
    
    # Iterate
    for _ in range(max_iter):
        new_pr = [0.0] * N
        
        for node in nodes:
            idx = node_to_idx[node]
            # Add restart probability
            new_pr[idx] = (1.0 - damping_factor) * p[idx]
            
        # Distribute PageRank along edges
        for node in nodes:
            idx = node_to_idx[node]
            out_deg = out_degree[node]
            
            if out_deg > 0:
                share = (damping_factor * pr[idx]) / out_deg
                for neighbor in graph.edges[node]:
                    n_idx = node_to_idx[neighbor]
                    new_pr[n_idx] += share
            else:
                # Dangling node (no outgoing edges) -> distribute its rank to everyone based on personalization
                share = damping_factor * pr[idx]
                for i in range(N):
                    new_pr[i] += share * p[i]
                    
        # Check convergence
        diff = sum(abs(new_pr[i] - pr[i]) for i in range(N))
        pr = new_pr
        
        if diff < tol:
            break
            
    # Sort and return
    result = [(nodes[i], pr[i]) for i in range(N)]
    result.sort(key=lambda x: x[1], reverse=True)
    return result
