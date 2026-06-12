import ast
from pathlib import Path
from typing import Dict, List, Set

class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self, current_module: str):
        self.current_module = current_module
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            base_module = node.module
            if node.level > 0:
                parts = self.current_module.split('.')
                base = ".".join(parts[:-node.level])
                if base:
                    base_module = f"{base}.{node.module}"
            
            for alias in node.names:
                self.imports.add(f"{base_module}.{alias.name}")
        else:
            if node.level > 0:
                parts = self.current_module.split('.')
                base = ".".join(parts[:-node.level])
                for alias in node.names:
                    if base:
                        self.imports.add(f"{base}.{alias.name}")
                    else:
                        self.imports.add(alias.name)
        self.generic_visit(node)

def build_import_graph(directory: str) -> Dict[str, List[str]]:
    """
    Scans a directory for python files and builds a dependency graph mapping
    module names to the list of modules they import.
    """
    root_path = Path(directory).resolve()
    graph = {}
    
    for py_file in root_path.rglob("*.py"):
        if "venv" in py_file.parts or ".venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
            
        try:
            rel_path = py_file.relative_to(root_path)
            # Convert a/b/c.py to a.b.c
            module_name = str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")
            if module_name.endswith(".__init__"):
                module_name = module_name[:-9]
                
            with open(py_file, "r", encoding="utf-8") as f:
                code = f.read()
                
            tree = ast.parse(code)
            analyzer = ImportAnalyzer(module_name)
            analyzer.visit(tree)
            
            graph[module_name] = list(analyzer.imports)
            
        except Exception:
            # Skip unparseable files
            continue
            
    return graph
