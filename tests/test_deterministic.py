import pytest
from acc.compression.deterministic import DeterministicCompressor

def test_deterministic_compression():
    compressor = DeterministicCompressor(max_tokens=2000)
    text = "aaa bbb ccc"
    compressed = compressor.run(text)
    assert compressed == text
