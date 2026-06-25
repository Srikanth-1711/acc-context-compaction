import pytest
from acc.compression.irc import InlineReversibleCompressor

def test_irc_roundtrip():
    irc = InlineReversibleCompressor()
    text = "Line 0\nLine 1\nLine 2\nLine 3\nLine 4"
    drop_indices = [1, 3]
    
    compressed = irc.compress(text, drop_indices)
    assert "irc:" in compressed
    assert "Line 1" not in compressed
    assert "Line 3" not in compressed
    assert "Line 0" in compressed
    
    expanded = irc.expand(compressed)
    assert expanded == text

def test_irc_external_fallback(monkeypatch):
    irc = InlineReversibleCompressor()
    
    # Generate long text that will exceed 200 char token
    long_lines = [f"This is an extremely long line {i} with a lot of varying entropy {i*10} so that zlib cannot compress it down to under 200 chars easily " * 100 for i in range(20)]
    text = "\n".join(long_lines)
    drop_indices = [2, 3, 4, 5, 6, 7]
    
    compressed = irc.compress(text, drop_indices)
    assert "ircref:" in compressed
    assert "irc:" not in compressed
    
    expanded = irc.expand(compressed)
    assert expanded == text

def test_irc_indexing_edge_case():
    irc = InlineReversibleCompressor()
    text = "Line 0\nLine 1\nLine 2\nLine 3\nLine 4"
    drop_indices = [0, 2, 4]  # Edge case where non-dropped indices are misaligned
    
    compressed = irc.compress(text, drop_indices)
    expanded = irc.expand(compressed)
    assert expanded == text
