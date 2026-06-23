import pytest
import os
import json
from pathlib import Path
from acc.compaction.pipeline import FilterPipeline
from acc.filters.toml_loader import is_trusted, trust_file, load_filters

def test_pipeline_strip_ansi():
    config = {
        "stages": [{"name": "strip_ansi"}]
    }
    pipeline = FilterPipeline(config)
    output = pipeline.run("Hello \x1B[31mWorld\x1B[0m")
    assert output == "Hello World"

def test_pipeline_regex_drop():
    config = {
        "stages": [
            {"name": "regex_drop", "pattern": "^drop"}
        ]
    }
    pipeline = FilterPipeline(config)
    output = pipeline.run("keep this\ndrop this\nkeep that")
    assert output == "keep this\nkeep that"

def test_pipeline_smart_truncate():
    config = {
        "stages": [
            {
                "name": "smart_truncate",
                "max_lines": 3,
                "head_ratio": 0.5,
                "priority_lines": "^error"
            }
        ]
    }
    pipeline = FilterPipeline(config)
    output = pipeline.run("line 1\nerror: bad\nline 3\nline 4\nline 5\nerror: worse")
    # Priority matches: "error: bad", "error: worse" (2 lines)
    # Remaining slots: 1.
    # rem_head = int(1 * 0.5) = 0
    # rem_tail = 1 - 0 = 1
    # Tail non-priority is "line 5".
    # Output should include priority lines and line 5.
    assert "error: bad" in output
    assert "error: worse" in output
    assert "line 5" in output
    assert pipeline.was_truncated is True
    assert "[Truncated. Full output saved to" in output

def test_pipeline_smart_truncate_edge_cases():
    from acc.compaction.pipeline import FilterPipeline
    pipeline = FilterPipeline()
    
    # no priority_lines
    res = pipeline._smart_truncate(["line1", "line2", "line3"], {"max_lines": 2}, "raw")
    assert len(res) == 3 # Truncated to 2 lines + 1 tee message
    
    # match everything
    res2 = pipeline._smart_truncate(["p1", "p2", "p3"], {"max_lines": 2, "priority_lines": "p"}, "raw")
    assert len(res2) == 3
    
    # empty
    res3 = pipeline._smart_truncate([], {"max_lines": 2}, "raw")
    assert len(res3) == 0

def test_pipeline_head_tail():
    from acc.compaction.pipeline import FilterPipeline
    pipeline = FilterPipeline()
    lines = ["a", "b", "c", "d"]
    # head 0
    res = pipeline._head_tail(lines, {"max_lines": 2, "head_ratio": 0.0}, "raw")
    assert res[0] == "c"
    
    # head 1
    res2 = pipeline._head_tail(lines, {"max_lines": 2, "head_ratio": 1.0}, "raw")
    assert res2[0] == "a"

def test_pipeline_on_empty():
    from acc.compaction.pipeline import FilterPipeline
    pipeline = FilterPipeline()
    assert pipeline._on_empty([], {"fallback": "f"}) == ["f"]
    assert pipeline._on_empty([""], {"fallback": "f"}) == ["f"]
    assert pipeline._on_empty([" ", ""], {"fallback": "f"}) == [" ", ""]

def test_pipeline_tee_truncate():
    from acc.compaction.pipeline import FilterPipeline
    import os
    pipeline = FilterPipeline()
    res = pipeline._tee_truncate(["line1"], "raw_data")
    assert pipeline.was_truncated is True
    assert pipeline.tee_path is not None
    assert os.path.exists(pipeline.tee_path)
    with open(pipeline.tee_path) as f:
        assert f.read() == "raw_data"
    os.remove(pipeline.tee_path)

def test_toml_loader_trust(tmp_path, monkeypatch):
    from acc.filters import toml_loader
    # Mock trusted file path
    trusted_file = tmp_path / "trusted.json"
    monkeypatch.setattr(toml_loader, "_get_trusted_file", lambda: trusted_file)

    toml_file = tmp_path / "filters.toml"
    toml_file.write_text('[filter.test]\ncommand="test"\n')

    assert not is_trusted(toml_file)
    
    with pytest.raises(ValueError, match="NOT trusted"):
        load_filters(toml_file)

    trust_file(toml_file)
    assert is_trusted(toml_file)

    config = load_filters(toml_file)
    assert config["filter"]["test"]["command"] == "test"
