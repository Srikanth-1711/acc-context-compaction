from acc.filters.strip_ansi import strip_ansi
from acc.filters.dedup import dedup
from acc.filters.noise import remove_noise
from acc.filters.head_tail import head_tail
from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager
import os
import yaml

def test_strip_ansi():
    lines = ["\x1b[31mError\x1b[0m", "Normal text"]
    res = strip_ansi(lines)
    assert res == ["Error", "Normal text"]

def test_dedup():
    lines = ["a", "a", "a", "b"]
    res = dedup(lines)
    assert "a (repeated 3 times)" in res
    assert "b" in res

def test_noise_default():
    lines = ["INFO  msg", "DEBUG trace", "hello world"]
    res = remove_noise(lines)
    assert res == ["hello world"]

def test_noise_custom():
    lines = ["Test collected 3 items", "FAILURES"]
    res = remove_noise(lines, custom_patterns=["collected "])
    assert res == ["FAILURES"]

def test_head_tail():
    lines = [f"line {i}" for i in range(100)]
    res = head_tail(lines, max_lines=10, head_ratio=0.2)
    assert len(res) == 11
    assert res[0] == "line 0"
    assert res[-1] == "line 99"

def test_pipeline_with_profile(tmp_path):
    # Mock a profile yaml
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    profile_file = profile_dir / "test.yaml"
    with open(profile_file, "w") as f:
        yaml.dump({"noise_patterns": ["ignore_me"], "max_lines": 5}, f)
        
    pm = ProfileManager(str(profile_dir))
    profile = pm.load_profile("test")
    
    pipeline = FilterPipeline(profile)
    text = "line 1\nignore_me please\nline 2"
    res = pipeline.execute(text)
    
    assert "ignore_me" not in res
    assert "line 1" in res
