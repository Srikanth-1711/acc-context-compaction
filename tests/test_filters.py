from acc.filters.strip_ansi import strip_ansi
from acc.filters.dedup import dedup
from acc.filters.noise import remove_noise
from acc.filters.head_tail import head_tail
from acc.filters.pipeline import FilterPipeline

def test_strip_ansi():
    lines = ["\x1b[31mError\x1b[0m", "Normal text"]
    res = strip_ansi(lines)
    assert res == ["Error", "Normal text"]

def test_dedup():
    lines = ["a", "a", "a", "b"]
    res = dedup(lines)
    assert "a (repeated 3 times)" in res
    assert "b" in res

def test_noise():
    lines = ["INFO  msg", "DEBUG trace", "hello world"]
    res = remove_noise(lines)
    assert res == ["hello world"]

def test_head_tail():
    lines = [f"line {i}" for i in range(100)]
    res = head_tail(lines, max_lines=10, head_ratio=0.2)
    assert len(res) == 11 # 2 head + 1 truncate msg + 8 tail
    assert res[0] == "line 0"
    assert res[-1] == "line 99"
    assert "truncated" in res[2]

def test_pipeline():
    pipeline = FilterPipeline()
    text = "\x1b[31mINFO  Starting...\x1b[0m\nError occurred\nError occurred\nError occurred"
    res = pipeline.execute(text)
    assert "INFO" not in res
    assert "Error occurred (repeated 3 times)" in res
