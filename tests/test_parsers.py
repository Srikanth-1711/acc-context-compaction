"""Tests for backward compatibility — parser routing via get_parser."""
from acc.compaction.parsers import get_parser


def test_git_parser_exists():
    parser = get_parser("git")
    assert parser is not None


def test_pytest_parser_exists():
    parser = get_parser("pytest")
    assert parser is not None

