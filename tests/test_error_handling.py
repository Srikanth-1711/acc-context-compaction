import pytest
import logging
import json
import os
from acc.compaction.pipeline import FilterPipeline
from acc.telemetry.tracker import AnalyticsTracker
from acc.compaction.dedup import DedupCache

def test_pipeline_invalid_regex_logs_warning(caplog):
    caplog.set_level(logging.WARNING)
    pipeline = FilterPipeline({"stages": [{"name": "regex_replace", "pattern": "[invalid"}]})
    pipeline.run("test")
    assert "Invalid regex pattern" in caplog.text

def test_toml_loader_corrupt_trusted_json_logs_error(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    import acc.filters.toml_loader as toml_loader
    
    trusted_file = tmp_path / ".acc" / "trusted.json"
    trusted_file.parent.mkdir(parents=True, exist_ok=True)
    trusted_file.write_text("{bad json")
    monkeypatch.setattr(toml_loader, "_get_trusted_file", lambda: trusted_file)
    
    filters_file = tmp_path / "filters.toml"
    filters_file.write_text("content")
    
    assert toml_loader.is_trusted(filters_file) is False
    assert "Failed to read trusted hashes" in caplog.text

def test_tracker_db_error_does_not_crash(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    
    def mock_session(*args, **kwargs):
        raise Exception("DB is broken")
        
    import acc.telemetry.tracker as tracker_mod
    monkeypatch.setattr(tracker_mod, "Session", mock_session)
    
    from acc.mcp_server import acc_run
    
    from acc.compaction.executor import ExecutionResult
    import acc.mcp_server as mcp_server
    monkeypatch.setattr(mcp_server, "execute_command", lambda x: ExecutionResult(stdout="hi", exit_code=0))
    
    class MockRetriever:
        def __init__(self, *args, **kwargs): pass
        def temporal_query(self, *args, **kwargs): return []
    monkeypatch.setattr(mcp_server, "MemoryRetriever", MockRetriever)
    
    acc_run("cmd")
    assert "Telemetry logging failed" in caplog.text

def test_dedup_save_error_logs_but_does_not_crash(tmp_path, monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    import tempfile
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    
    cache = DedupCache("test_session")
    
    def mock_replace(*args, **kwargs):
        raise OSError("Mock save error")
    monkeypatch.setattr("os.replace", mock_replace)
    
    cache.check("test text")
    assert "Failed to save dedup cache" in caplog.text
