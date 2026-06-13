"""Tests for the session-scoped dedup cache."""

from acc.compaction.dedup_cache import DedupCache, Fingerprint


def test_same_input_suppressed():
    cache = DedupCache()
    cache.next_turn()

    text = "This is some output from a command"
    # First check — should pass through
    result1 = cache.check(text)
    assert result1 is None

    # Second check with same text — should be suppressed
    cache.next_turn()
    result2 = cache.check(text)
    assert result2 is not None
    assert "suppressed" in result2
    assert "turn #1" in result2


def test_different_input_passes():
    cache = DedupCache()
    cache.next_turn()

    result1 = cache.check("output A")
    assert result1 is None

    cache.next_turn()
    result2 = cache.check("output B")
    assert result2 is None  # Different content should pass


def test_empty_input_never_cached():
    cache = DedupCache()
    cache.next_turn()

    result1 = cache.check("")
    assert result1 is None

    cache.next_turn()
    result2 = cache.check("")
    assert result2 is None  # Empty should never suppress


def test_whitespace_only_never_cached():
    cache = DedupCache()
    cache.next_turn()

    result1 = cache.check("   \n  \n  ")
    assert result1 is None

    cache.next_turn()
    result2 = cache.check("   \n  \n  ")
    assert result2 is None  # Whitespace-only should never suppress


def test_clear_resets():
    cache = DedupCache()
    cache.next_turn()
    cache.check("some output")

    assert cache.size == 1
    assert cache.current_turn == 1

    cache.clear()
    assert cache.size == 0
    assert cache.current_turn == 0


def test_turn_counter_increments():
    cache = DedupCache()
    assert cache.current_turn == 0
    cache.next_turn()
    assert cache.current_turn == 1
    cache.next_turn()
    assert cache.current_turn == 2


def test_fingerprint_collision_resistance():
    """Same length but different content should NOT collide."""
    cache = DedupCache()
    cache.next_turn()

    # Two strings of same length but different content
    text_a = "A" * 500
    text_b = "B" * 500
    assert len(text_a) == len(text_b)

    result1 = cache.check(text_a)
    assert result1 is None

    cache.next_turn()
    result2 = cache.check(text_b)
    assert result2 is None  # Should NOT be suppressed


def test_file_dedup():
    cache = DedupCache()
    cache.next_turn()

    # First read
    result1 = cache.check_file("/path/to/file.py", size=1234, mtime_ns=9999)
    assert result1 is None

    # Same file, same stat — should suppress
    cache.next_turn()
    result2 = cache.check_file("/path/to/file.py", size=1234, mtime_ns=9999)
    assert result2 is not None
    assert "unchanged" in result2

    # Same file, different mtime — should pass
    cache.next_turn()
    result3 = cache.check_file("/path/to/file.py", size=1234, mtime_ns=10000)
    assert result3 is None


def test_file_dedup_different_path():
    cache = DedupCache()
    cache.next_turn()

    cache.check_file("/path/to/a.py", size=100, mtime_ns=1)
    cache.next_turn()
    result = cache.check_file("/path/to/b.py", size=100, mtime_ns=1)
    # Different path should not suppress even if same size/mtime
    assert result is None


def test_large_text_fingerprint():
    """Verify fingerprinting works on large inputs without reading entire content."""
    cache = DedupCache()
    cache.next_turn()

    large_text = "x" * 100_000
    result1 = cache.check(large_text)
    assert result1 is None

    cache.next_turn()
    result2 = cache.check(large_text)
    assert result2 is not None
    assert "100,000 bytes" in result2


def test_suppression_message_includes_byte_count():
    cache = DedupCache()
    cache.next_turn()
    cache.check("hello world")

    cache.next_turn()
    result = cache.check("hello world")
    assert "11 bytes" in result
