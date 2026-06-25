import pytest
from acc.compression.deterministic import DeterministicCompressor

def test_deterministic_compression():
    compressor = DeterministicCompressor()
    text = "aaa bbb ccc"
    compressed = compressor.run(text)
    assert compressed == text
