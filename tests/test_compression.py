import pytest
from acc.compression.deterministic import DeterministicCompressor

def test_compression_keeps_important_lines():
    compressor = DeterministicCompressor()
    text = """Running build...
Compiling module A
Compiling module C
Compiling module D
Compiling module E
Compiling module F
ERROR: Syntax error on line 5
Compiling module B
def calculate_score():
    pass
Finished dev build in 0.5s"""
    
    compressed = compressor.compress(text, target_ratio=0.5)
    
    assert "ERROR: Syntax error" in compressed
    assert "def calculate_score():" in compressed
    assert "Finished dev" not in compressed
    assert "dropped]" in compressed

def test_compression_preserves_short_text():
    compressor = DeterministicCompressor()
    text = "Short text\nwith\nonly\nfour\nlines."
    assert compressor.compress(text) == text

def test_compression_preserves_order():
    compressor = DeterministicCompressor()
    text = "\n".join([f"Line {i}" for i in range(20)])
    text += "\nERROR: final error"
    
    compressed = compressor.compress(text, target_ratio=0.3)
    lines = compressed.split('\n')
    
    error_idx = [i for i, line in enumerate(lines) if "ERROR" in line]
    assert len(error_idx) == 1
    assert error_idx[0] == len(lines) - 1  # Should be the last line
