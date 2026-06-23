import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

from acc.repo.treesitter_utils import (
    has_treesitter, get_language, ts_extract_name, 
    TS_FUNC_TYPES, TS_CALL_TYPES
)

class Node:
    def __init__(self, name: str, file_path: str, line: int):
        self.name = name
        self.file_path = file_path
        self.line = line

    def __hash__(self):
        return hash((self.name, self.file_path))

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.name == other.name and self.file_path == other.file_path

    def __repr__(self):
        return f"{self.name} ({os.path.basename(self.file_path)}:{self.line})"

class SymbolGraph:
    def __init__(self):
        self.nodes: Set[Node] = set()
        # Edge: node -> set of nodes it calls
        self.edges: Dict[Node, Set[Node]] = {}
        # Reverse lookup: symbol name -> list of Nodes (handling same name in different files)
        self.name_to_nodes: Dict[str, List[Node]] = {}

    def add_node(self, node: Node):
        if node not in self.nodes:
            self.nodes.add(node)
            self.edges[node] = set()
            if node.name not in self.name_to_nodes:
                self.name_to_nodes[node.name] = []
            self.name_to_nodes[node.name].append(node)

    def add_edge(self, caller: Node, callee: Node):
        if caller in self.edges:
            self.edges[caller].add(callee)

def build_symbol_graph(directory: str) -> SymbolGraph:
    """Builds a symbol graph for the entire repository using tree-sitter."""
    if not has_treesitter():
        raise ImportError("tree-sitter-languages is required for SymbolGraph.")
        
    from tree_sitter_languages import get_parser
    
    root_path = Path(directory).resolve()
    graph = SymbolGraph()
    
    # Pass 1: Extract all symbols (nodes)
    for file_path in root_path.rglob("*"):
        if file_path.is_dir() or "venv" in file_path.parts or ".venv" in file_path.parts or "__pycache__" in file_path.parts:
            continue
            
        lang = get_language(str(file_path))
        if not lang:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            continue
            
        try:
            parser = get_parser(lang)
            tree = parser.parse(source.encode("utf-8"))
            
            func_types = set(TS_FUNC_TYPES.get(lang, []))
            
            def _extract_nodes(node):
                if node.type in func_types:
                    name = ts_extract_name(node, source)
                    # For classes, we might just store the class name
                    n = Node(name, str(file_path), node.start_point[0] + 1)
                    graph.add_node(n)
                
                for child in node.children:
                    _extract_nodes(child)
                    
            _extract_nodes(tree.root_node)
        except Exception as e:
            # Skip files that fail to parse
            pass

    # Pass 2: Extract calls (edges)
    for file_path in root_path.rglob("*"):
        if file_path.is_dir() or "venv" in file_path.parts or ".venv" in file_path.parts or "__pycache__" in file_path.parts:
            continue
            
        lang = get_language(str(file_path))
        if not lang:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception:
            continue
            
        try:
            parser = get_parser(lang)
            tree = parser.parse(source.encode("utf-8"))
            
            func_types = set(TS_FUNC_TYPES.get(lang, []))
            call_types = set(TS_CALL_TYPES.get(lang, []))
            
            # Keep track of the current function context
            def _extract_edges(node, current_context_node=None):
                new_context = current_context_node
                
                if node.type in func_types:
                    name = ts_extract_name(node, source)
                    # Find the corresponding Node
                    potentials = graph.name_to_nodes.get(name, [])
                    for p in potentials:
                        if p.file_path == str(file_path) and p.line == node.start_point[0] + 1:
                            new_context = p
                            break
                            
                elif node.type in call_types and current_context_node:
                    # Extract the called function name
                    # In tree-sitter, the first child is usually the identifier
                    # e.g., call_expression -> identifier, argument_list
                    # This is naive but works for simple cases
                    called_name = ts_extract_name(node, source)
                    
                    # If this called function exists in our graph, add an edge
                    if called_name in graph.name_to_nodes:
                        # We might have multiple targets (e.g., same name in different files)
                        # We just add an edge to all of them for now (naive resolution)
                        for target in graph.name_to_nodes[called_name]:
                            graph.add_edge(current_context_node, target)
                            
                for child in node.children:
                    _extract_edges(child, new_context)
                    
            _extract_edges(tree.root_node)
        except Exception as e:
            pass
            
    return graph
