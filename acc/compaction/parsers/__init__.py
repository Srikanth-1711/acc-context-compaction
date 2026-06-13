"""
Auto-discovery module for parser plugins.

Scans this directory for modules containing BaseParser subclasses,
instantiates them, and builds a registry keyed by tool name.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Optional

from acc.compaction.parsers.base import BaseParser

_registry: list[BaseParser] = []
_initialized = False


def _discover_parsers():
    """Import all modules in this package and collect BaseParser subclasses."""
    global _initialized
    if _initialized:
        return

    package_dir = Path(__file__).parent
    for finder, module_name, is_pkg in pkgutil.iter_modules([str(package_dir)]):
        if module_name in ("base", "__init__"):
            continue
        module = importlib.import_module(f"acc.compaction.parsers.{module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseParser)
                and attr is not BaseParser
                and attr.tool_names  # skip abstract or empty
            ):
                _registry.append(attr())

    _initialized = True


def get_parser(command: str) -> Optional[BaseParser]:
    """
    Find a parser that can handle the given command name.
    Returns None if no parser matches.
    """
    _discover_parsers()
    for parser in _registry:
        if parser.can_handle(command):
            return parser
    return None


def get_all_parsers() -> list[BaseParser]:
    """Return all registered parsers. Useful for testing."""
    _discover_parsers()
    return list(_registry)
