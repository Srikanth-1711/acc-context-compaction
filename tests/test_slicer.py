"""Tests for the multi-language file slicer."""

import os
from pathlib import Path

import pytest
from acc.compaction.slicer import slice_file


def test_slice_python_stdlib_ast(tmp_path: Path):
    """Test Python slicing with stdlib ast."""
    source = '''
import os
from pathlib import Path

MAX_RETRIES = 3

class MyClass(Base):
    def method(self):
        pass

def target_func(x: int) -> int:
    """Target function."""
    y = x + 1
    return y

async def async_func():
    await asyncio.sleep(1)
'''
    py_file = tmp_path / "test.py"
    py_file.write_text(source)

    # 1. Without focus function
    result = slice_file(str(py_file))
    assert "[IMPORTS] os, pathlib.Path" in result
    assert "[CLASSES] MyClass(Base)" in result
    assert "target_func(" in result
    assert "def target_func(x: int) -> int" in result
    assert "async_func(" in result
    assert "async def async_func()" in result
    assert "MAX_RETRIES=3" in result
    assert "y = x + 1" not in result  # Body should not be included

    # 2. With focus function
    from acc.compaction.dedup_cache import get_session_cache
    get_session_cache().clear()
    
    result_focused = slice_file(str(py_file), focus_function="target_func")
    assert "FULL IMPLEMENTATION" in result_focused
    assert "y = x + 1" in result_focused  # Body should be included
    assert "def method" in result_focused  # Signatures still present


def test_slice_unsupported_language_fallback(tmp_path: Path):
    """Test fallback to raw truncation for unsupported extensions."""
    source = "line\n" * 150
    txt_file = tmp_path / "test.txt"
    txt_file.write_text(source)

    result = slice_file(str(txt_file))
    assert "[TRUNCATED]" in result
    assert "lines truncated" in result


def test_slice_dedup_cache(tmp_path: Path):
    """Test O(1) file stat deduplication."""
    from acc.compaction.dedup_cache import get_session_cache
    
    # Reset cache
    get_session_cache().clear()
    
    source = "def func(): pass\n"
    py_file = tmp_path / "dedup.py"
    py_file.write_text(source)
    
    get_session_cache().next_turn()
    res1 = slice_file(str(py_file))
    assert "[FUNCTIONS]" in res1
    
    get_session_cache().next_turn()
    res2 = slice_file(str(py_file))
    assert "File unchanged" in res2
    assert "suppressed" in res2


@pytest.mark.skipif(
    not __import__("acc.compaction.slicer").compaction.slicer._has_treesitter(),
    reason="tree-sitter-languages not installed",
)
def test_slice_treesitter_javascript(tmp_path: Path):
    """Test JS slicing with tree-sitter."""
    source = '''
import { useState } from 'react';
import axios from 'axios';

const API_URL = "https://api.example.com";

class ApiClient {
    constructor() {}
}

function fetchData(id) {
    console.log("fetching", id);
    return true;
}

const arrowFunc = () => { return false; }
'''
    js_file = tmp_path / "test.js"
    js_file.write_text(source)

    # Need to bypass dedup cache so it actually reads the file
    from acc.compaction.dedup_cache import get_session_cache
    get_session_cache().clear()

    result = slice_file(str(js_file))
    
    assert "react" in result
    assert "axios" in result
    assert "ApiClient" in result
    assert "fetchData" in result
    assert "arrowFunc" in result
    assert "console.log" not in result  # Body should not be included

    # With focus function
    get_session_cache().clear()
    result_focused = slice_file(str(js_file), focus_function="fetchData")
    assert "FULL IMPLEMENTATION" in result_focused
    assert "console.log(\"fetching\", id);" in result_focused
