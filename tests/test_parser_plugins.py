"""Tests for the plugin parser system."""

from acc.compaction.parsers import get_parser, get_all_parsers
from acc.compaction.parsers.base import BaseParser
from acc.compaction.parsers.pytest_parser import PytestParser
from acc.compaction.parsers.compiler_parser import CompilerParser
from acc.compaction.parsers.git_diff_parser import GitDiffParser
from acc.compaction.parsers.linter_parser import LinterParser
from acc.compaction.parsers.build_parser import BuildParser


# ── Auto-discovery tests ──

def test_auto_discovery_finds_all_parsers():
    parsers = get_all_parsers()
    names = {type(p).__name__ for p in parsers}
    assert "PytestParser" in names
    assert "CompilerParser" in names
    assert "GitDiffParser" in names
    assert "LinterParser" in names
    assert "BuildParser" in names


def test_get_parser_by_name():
    assert isinstance(get_parser("pytest"), PytestParser)
    assert isinstance(get_parser("gcc"), CompilerParser)
    assert isinstance(get_parser("clang++"), CompilerParser)
    assert isinstance(get_parser("git"), GitDiffParser)
    assert isinstance(get_parser("eslint"), LinterParser)
    assert isinstance(get_parser("ruff"), LinterParser)
    assert isinstance(get_parser("make"), BuildParser)
    assert isinstance(get_parser("ninja"), BuildParser)


def test_get_parser_unknown_returns_none():
    assert get_parser("some_unknown_tool_xyz") is None


def test_get_parser_handles_exe_suffix():
    assert isinstance(get_parser("pytest.exe"), PytestParser)
    assert isinstance(get_parser("gcc.exe"), CompilerParser)


# ── PytestParser tests ──

PYTEST_TEXT_OUTPUT = """============================= test session starts =============================
platform linux -- Python 3.10.0, pytest-7.4.0
collected 150 items

tests/test_a.py ............................................................. [ 40%]
tests/test_b.py ............................................................. [ 80%]
tests/test_critical.py F                                                      [ 81%]
tests/test_db.py F                                                            [ 82%]
tests/test_c.py ......................... PASSED                               [100%]

================================ short test summary info =================================
FAILED tests/test_critical.py::test_auth - AssertionError: 401 != 200
FAILED tests/test_db.py::test_connection - sqlalchemy.exc.OperationalError: Connection refused
================================= 2 failed, 148 passed ==================================
"""

def test_pytest_parser_text():
    parser = PytestParser()
    result = parser.parse(PYTEST_TEXT_OUTPUT)
    assert "[PYTEST]" in result
    assert "FAILED tests/test_critical.py::test_auth" in result
    assert "FAILED tests/test_db.py::test_connection" in result
    assert "passed tests suppressed" in result
    # Should NOT contain all the passing dots
    assert "........................" not in result


def test_pytest_parser_empty():
    parser = PytestParser()
    result = parser.parse("")
    assert "[PYTEST]" in result
    assert "No failures" in result


def test_pytest_parser_json():
    import json
    data = json.dumps({
        "summary": {"total": 10, "passed": 8, "failed": 2},
        "tests": [
            {"nodeid": "test_a.py::test_one", "outcome": "passed"},
            {"nodeid": "test_b.py::test_two", "outcome": "failed",
             "call": {"crash": {"message": "assert False"}}},
        ]
    })
    parser = PytestParser()
    result = parser.parse(data)
    assert "[PYTEST]" in result
    assert "test_b.py::test_two" in result
    assert "assert False" in result


# ── CompilerParser tests ──

GCC_OUTPUT = """main.c: In function 'main':
main.c:10:5: error: 'foo' undeclared (first use in this function)
main.c:10:5: note: each undeclared identifier is reported only once
main.c:15:5: error: 'foo' undeclared (first use in this function)
main.c:20:3: warning: unused variable 'x' [-Wunused-variable]
In file included from header.h:1,
                 from main.c:2:
util.h:5:1: warning: implicit declaration of function 'bar'
"""

def test_compiler_parser_text():
    parser = CompilerParser()
    result = parser.parse(GCC_OUTPUT)
    assert "[BUILD]" in result
    assert "error" in result.lower()
    # Note: lines should be dropped
    assert "each undeclared identifier" not in result
    # Include traces should be dropped
    assert "In file included from" not in result


def test_compiler_parser_empty():
    parser = CompilerParser()
    result = parser.parse("")
    assert "[BUILD]" in result
    assert "0 error" in result


# ── GitDiffParser tests ──

GIT_DIFF_WITH_WHITESPACE = """diff --git a/file.py b/file.py
index abc..def 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 def foo():
-    
+
     return 1
"""

GIT_DIFF_WITH_CRITICAL = """diff --git a/server.py b/server.py
index abc..def 100644
--- a/server.py
+++ b/server.py
@@ -10,3 +10,5 @@
 def handle():
+    mutex.acquire()
     process()
+    mutex.release()
"""

def test_git_diff_skips_whitespace_hunks():
    parser = GitDiffParser()
    result = parser.parse(GIT_DIFF_WITH_WHITESPACE)
    assert "[DIFF]" in result
    assert "whitespace" in result.lower() or "0 shown" in result


def test_git_diff_marks_critical():
    parser = GitDiffParser()
    result = parser.parse(GIT_DIFF_WITH_CRITICAL)
    assert "CRITICAL" in result
    assert "mutex" in result


def test_git_diff_non_diff_passthrough():
    parser = GitDiffParser()
    git_log = "abc1234 Initial commit\ndef5678 Add feature"
    result = parser.parse(git_log)
    # Non-diff git output should pass through unchanged
    assert result == git_log


# ── LinterParser tests ──

RUFF_OUTPUT = """main.py:1:1: F401 `os` imported but unused
main.py:5:1: E302 expected 2 blank lines, got 1
main.py:10:1: W291 trailing whitespace
main.py:15:1: F401 `sys` imported but unused
main.py:20:1: F401 `json` imported but unused
main.py:25:1: F401 `re` imported but unused
main.py:30:1: F401 `math` imported but unused
main.py:35:1: F401 `time` imported but unused
"""

def test_linter_parser_text():
    parser = LinterParser()
    result = parser.parse(RUFF_OUTPUT)
    assert "[LINT]" in result
    assert "error" in result.lower()
    # F401 fires > 5 times, should be collapsed
    assert "total occurrences" in result


def test_linter_parser_empty():
    parser = LinterParser()
    result = parser.parse("")
    assert "[LINT]" in result
    assert "0 error" in result


# ── BuildParser tests ──

MAKE_SUCCESS = """make[1]: Entering directory '/build'
Compiling main.c
Compiling utils.c
Linking main
Built target main
make[1]: Leaving directory '/build'
"""

MAKE_FAILURE = """make[1]: Entering directory '/build'
Compiling main.c
Compiling utils.c
utils.c:45: error: implicit declaration of function 'foo'
make[2]: *** [utils.o] Error 1
make[1]: Leaving directory '/build'
"""

def test_build_parser_success():
    parser = BuildParser()
    result = parser.parse(MAKE_SUCCESS)
    assert "[BUILD OK]" in result
    assert "suppressed" in result


def test_build_parser_failure():
    parser = BuildParser()
    result = parser.parse(MAKE_FAILURE)
    assert "[BUILD FAILED]" in result
    assert "error" in result.lower()
    # Noise lines should be dropped from context
    assert "Entering directory" not in result


# ── Fallback test ──

def test_parser_fallback_on_exception():
    """Ensure parsers return raw output on internal failure."""
    parser = PytestParser()
    # Passing something that's not parseable but won't error
    result = parser.parse("this is just random text with no structure at all")
    # Should still return something useful, not raise
    assert "[PYTEST]" in result or "random text" in result
