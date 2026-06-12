from acc.filters.reduction import filter_noise, dedup, truncate

def test_filter_noise():
    lines = ["INFO   msg", "DEBUG  trace", "hello world"]
    res = filter_noise(lines)
    assert res == ["hello world"]

def test_dedup():
    lines = ["a", "a", "a", "b"]
    res = dedup(lines)
    assert "a (repeated 2 times)" in res
    assert "b" in res

def test_truncate():
    lines = [str(i) for i in range(10)]
    res = truncate(lines, max_lines=4)
    assert len(res) == 5
    assert res[0] == "0"
    assert res[-1] == "9"
    assert "snip" in res[2]
