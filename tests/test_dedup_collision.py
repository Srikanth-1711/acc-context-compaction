import pytest
import os
from acc.compaction.dedup import DedupCache

def test_dedup_collision(tmp_path, monkeypatch):
    # Use tmp_path for cache
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    
    cache = DedupCache("test_session")
    
    text1 = "This is a test output from a command."
    text2 = "This is a test output from a command!"  # Slight difference
    text3 = "Completely different text."
    
    cache.check(text1)
    
    # Same text should return identical marker
    assert cache.check(text1) is not None
    assert "identical to turn #0" in cache.check(text1)
    
    # Different texts should not collide
    assert cache.check(text2) is None
    assert cache.check(text3) is None

def test_dedup_length_edge_cases(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    cache = DedupCache("test_session2")
    
    # Empty string
    cache.check("")
    assert cache.check("") is not None
    
    # Long text
    long_text = "A" * 10000
    cache.check(long_text)
    assert cache.check(long_text) is not None
    
    # Another long text, slight difference
    long_text2 = "A" * 9999 + "B"
    assert cache.check(long_text2) is None
