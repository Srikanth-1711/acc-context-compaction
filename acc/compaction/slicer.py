"""
File slicer: returns a structural index of any supported source file.

Uses tree-sitter if available for multi-language support.
Falls back to stdlib ast for Python files.
Falls back to raw truncation for unsupported languages.

tree-sitter is an OPTIONAL dependency:
    pip install acc[slicer]
"""

import ast
import os
from pathlib import Path
from typing import Optional

from acc.compaction.dedup_cache import get_session_cache
from acc.repo.treesitter_utils import (
    has_treesitter, get_language, ts_extract_name, 
    TS_FUNC_TYPES, TS_IMPORT_TYPES
)


def slice_file(file_path: str, focus_function: Optional[str] = None) -> str:
    """
    Return a structural index of a source file.

    - All imports/includes
    - All class/struct definitions (name + line)
    - All function/method signatures (name + line)
    - Full implementation of focus_function if specified
    - Signature-only for everything else

    Uses tree-sitter for non-Python languages if installed,
    falls back to stdlib ast for Python, raw truncation for others.
    """
    file_path = str(Path(file_path).resolve())

    if not os.path.isfile(file_path):
        return f"[ERROR] File not found: {file_path}"

    # Check dedup cache first — O(1) via file stat
    cache = get_session_cache()
    try:
        stat = os.stat(file_path)
        suppressed = cache.check_file(file_path, stat.st_size, stat.st_mtime_ns)
        if suppressed:
            return suppressed
    except OSError:
        pass  # Can't stat — proceed with read

    lang = get_language(file_path)

    if lang is None:
        return _raw_truncated(file_path)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception as e:
        return f"[ERROR] Cannot read {file_path}: {e}"

    line_count = source.count("\n") + 1

    if lang == "python":
        return _slice_python(file_path, source, line_count, focus_function)

    # Try tree-sitter for non-Python languages
    if has_treesitter():
        try:
            return _slice_treesitter(
                file_path, source, lang, line_count, focus_function
            )
        except Exception:
            pass  # Fall through to raw truncation

    return _raw_truncated(file_path, source, line_count)


def _slice_python(
    file_path: str,
    source: str,
    line_count: int,
    focus_function: Optional[str] = None,
) -> str:
    """Slice a Python file using stdlib ast module."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _raw_truncated(file_path, source, line_count)

    lines = source.split("\n")
    imports = []
    classes = []
    functions = []
    constants = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Reconstruct import line
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            else:
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(
                ast.unparse(b) for b in node.bases
            ) if node.bases else ""
            sig = f"{node.name}({bases})" if bases else node.name
            classes.append((sig, node.lineno))

        elif isinstance(node, ast.FunctionDef) or isinstance(
            node, ast.AsyncFunctionDef
        ):
            # Build signature
            args = ast.unparse(node.args) if node.args.args else ""
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            sig = f"{prefix} {node.name}({args}){returns}"
            functions.append((node.name, sig, node.lineno, node.end_lineno or node.lineno))

        elif isinstance(node, ast.Assign) and isinstance(node, ast.Assign):
            # Top-level constants (module-level assignments with UPPER_CASE names)
            if hasattr(node, "lineno"):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        try:
                            val = ast.unparse(node.value)
                            if len(val) < 50:  # Don't show huge values
                                constants.append(
                                    f"{target.id}={val}(L{node.lineno})"
                                )
                        except Exception:
                            constants.append(
                                f"{target.id}=...(L{node.lineno})"
                            )

    return _format_index(
        file_path, line_count, source, imports, classes,
        functions, constants, focus_function, lines,
    )


def _slice_treesitter(
    file_path: str,
    source: str,
    lang: str,
    line_count: int,
    focus_function: Optional[str] = None,
) -> str:
    """Slice a file using tree-sitter."""
    from tree_sitter_languages import get_parser as ts_get_parser

    parser = ts_get_parser(lang)
    tree = parser.parse(source.encode("utf-8"))
    root = tree.root_node
    lines = source.split("\n")

    imports = []
    classes = []
    functions = []
    constants = []

    import_types = set(TS_IMPORT_TYPES.get(lang, []))
    func_types = set(TS_FUNC_TYPES.get(lang, []))

    def _walk(node):
        if node.type in import_types:
            text = source[node.start_byte:node.end_byte].strip()
            # Shorten long imports
            if len(text) > 80:
                text = text[:77] + "..."
            imports.append(text)

        elif node.type in func_types:
            name = ts_extract_name(node, source)
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            if "class" in node.type or "struct" in node.type or "enum" in node.type or "impl" in node.type:
                classes.append((name, start_line))
            else:
                # Extract signature (first line only)
                sig = lines[start_line - 1].strip() if start_line <= len(lines) else name
                functions.append((name, sig, start_line, end_line))

        for child in node.children:
            _walk(child)

    _walk(root)

    return _format_index(
        file_path, line_count, source, imports, classes,
        functions, constants, focus_function, lines,
    )



def _format_index(
    file_path: str,
    line_count: int,
    source: str,
    imports: list,
    classes: list,
    functions: list,
    constants: list,
    focus_function: Optional[str],
    lines: list[str],
) -> str:
    """Format the structural index output."""
    from acc.evals.harness import count_tokens

    raw_tokens = count_tokens(source)

    result = []

    # Find focus function body
    focus_body = None
    focus_tokens = 0
    if focus_function:
        for name, sig, start, end in functions:
            if name == focus_function:
                body_lines = lines[start - 1 : end]
                focus_body = "\n".join(body_lines)
                focus_tokens = count_tokens(focus_body)
                break

    # Build output
    served_estimate = 0  # Will count at end

    result.append(f"[FILE] {Path(file_path).name} ({line_count} lines, ~{raw_tokens:,} tokens raw)")

    if imports:
        # Deduplicate and shorten
        unique_imports = list(dict.fromkeys(imports))[:20]
        result.append(f"[IMPORTS] {', '.join(unique_imports)}")

    if classes:
        class_strs = [f"{name}(L{line})" for name, line in classes]
        result.append(f"[CLASSES] {', '.join(class_strs)}")

    if functions:
        result.append("[FUNCTIONS]")
        for name, sig, start, end in functions:
            if focus_function and name == focus_function:
                result.append(f"  → {name}(L{start}-L{end}): FULL IMPLEMENTATION")
                if focus_body:
                    result.append(focus_body)
            else:
                result.append(f"  {name}(L{start}): {sig}")

    if constants:
        result.append(f"[CONSTANTS] {', '.join(constants[:10])}")

    output = "\n".join(result)
    served_tokens = count_tokens(output)
    reduction_pct = (1 - served_tokens / max(raw_tokens, 1)) * 100

    # Prepend serving stats
    header = f"[SERVING] ~{served_tokens:,} tokens ({reduction_pct:.0f}% reduction)"
    result.insert(1, header)

    return "\n".join(result)


def _raw_truncated(
    file_path: str,
    source: Optional[str] = None,
    line_count: Optional[int] = None,
) -> str:
    """Fallback: return head + tail of the file."""
    if source is None:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
        except Exception as e:
            return f"[ERROR] Cannot read {file_path}: {e}"

    lines = source.split("\n")
    if line_count is None:
        line_count = len(lines)

    if line_count <= 100:
        return source

    head = lines[:50]
    tail = lines[-50:]
    return "\n".join(
        [f"[FILE] {Path(file_path).name} ({line_count} lines)"]
        + [f"[TRUNCATED] Showing first 50 + last 50 lines"]
        + head
        + [f"\n... [{line_count - 100} lines truncated] ...\n"]
        + tail
    )
