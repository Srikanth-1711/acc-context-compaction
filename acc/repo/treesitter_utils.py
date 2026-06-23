import os
from typing import Optional

# Language detection from file extension
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
}

# tree-sitter node types for function/class extraction by language
TS_FUNC_TYPES = {
    "python": ["function_definition", "class_definition"],
    "javascript": ["function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "function"],
    "typescript": ["function_declaration", "class_declaration", "method_definition",
                   "arrow_function", "function"],
    "c": ["function_definition", "struct_specifier", "enum_specifier"],
    "cpp": ["function_definition", "class_specifier", "struct_specifier"],
    "rust": ["function_item", "struct_item", "enum_item", "impl_item"],
    "go": ["function_declaration", "method_declaration", "type_declaration"],
    "java": ["method_declaration", "class_declaration", "interface_declaration"],
}

TS_IMPORT_TYPES = {
    "python": ["import_statement", "import_from_statement"],
    "javascript": ["import_statement"],
    "typescript": ["import_statement"],
    "c": ["preproc_include"],
    "cpp": ["preproc_include", "using_declaration"],
    "rust": ["use_declaration"],
    "go": ["import_declaration"],
    "java": ["import_declaration"],
}

TS_CALL_TYPES = {
    "python": ["call"],
    "javascript": ["call_expression"],
    "typescript": ["call_expression"],
    "c": ["call_expression"],
    "cpp": ["call_expression"],
    "rust": ["call_expression"],
    "go": ["call_expression"],
    "java": ["method_invocation"],
}

def has_treesitter() -> bool:
    """Check if tree-sitter-languages is installed."""
    try:
        import tree_sitter_languages  # noqa: F401
        return True
    except ImportError:
        return False

def get_language(file_path: str) -> Optional[str]:
    ext = os.path.splitext(file_path)[1].lower()
    return EXTENSION_MAP.get(ext)

def ts_extract_name(node, source: str) -> str:
    """Extract the name identifier from a tree-sitter node."""
    for child in node.children:
        if child.type in ("identifier", "name", "type_identifier", "field_identifier"):
            return source[child.start_byte:child.end_byte]
    # Fallback: return first meaningful text
    text = source[node.start_byte:node.end_byte]
    first_line = text.split("\n")[0].strip()
    return first_line[:60] if len(first_line) > 60 else first_line
