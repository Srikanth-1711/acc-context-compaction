import pytest
import os
from pathlib import Path
from sqlmodel import Session, select
from acc.telemetry.models import RunLog

def test_tracker_log_run(tmp_path, monkeypatch):
    from acc.telemetry import tracker
    
    # Mock database path
    db_path = tmp_path / "acc_telemetry.db"
    def mock_get_engine():
        from sqlmodel import create_engine
        return create_engine(f"sqlite:///{db_path}")
        
    monkeypatch.setattr(tracker, "get_engine", mock_get_engine)
    
    from acc.mcp_server import count_tokens
    
    analytics = tracker.AnalyticsTracker()
    raw_txt = "git status" * 50
    out_txt = "git status" * 5
    raw_tokens = count_tokens(raw_txt)
    output_tokens = count_tokens(out_txt)
    
    analytics.log_run("git status", raw_tokens, output_tokens, deduped=False)
    
    with Session(analytics.engine) as session:
        logs = session.exec(select(RunLog)).all()
        assert len(logs) == 1
        assert logs[0].command == "git status"
        assert logs[0].raw_tokens == raw_tokens
        assert logs[0].output_tokens == output_tokens
        assert logs[0].compression_ratio == output_tokens / raw_tokens

def test_tracker_get_json(tmp_path, monkeypatch):
    from acc.telemetry import tracker
    
    db_path = tmp_path / "acc_telemetry.db"
    monkeypatch.setattr(tracker, "get_engine", lambda: __import__('sqlmodel').create_engine(f"sqlite:///{db_path}"))
    
    analytics = tracker.AnalyticsTracker()
    analytics.log_run("cargo build", 5000, 500)
    analytics.log_run("pytest", 1000, 100)
    
    res = analytics.get_json("all")
    assert res["runs"] == 2
    assert res["raw_tokens"] == 6000
    assert res["output_tokens"] == 600
    assert res["saved_tokens"] == 5400
    assert res["reduction_pct"] == 90.0

def test_tracker_markdown(tmp_path, monkeypatch):
    from acc.telemetry import tracker
    
    db_path = tmp_path / "acc_telemetry.db"
    monkeypatch.setattr(tracker, "get_engine", lambda: __import__('sqlmodel').create_engine(f"sqlite:///{db_path}"))
    
    analytics = tracker.AnalyticsTracker()
    analytics.log_run("cargo build", 5000, 500)
    
    md = analytics.get_markdown_report()
    assert "ACC Telemetry Analytics" in md
    assert "5,000" in md
    assert "500" in md
    assert "90.0%" in md

def test_tiktoken_vs_fallback():
    from acc.mcp_server import count_tokens
    code = "def foo():\n    pass"
    tokens = count_tokens(code)
    # tiktoken should count this as ~6-8 tokens, not len//4 = 3
    assert tokens > len(code) // 4

def test_tracker_errors(monkeypatch):
    from acc.telemetry.tracker import AnalyticsTracker
    import acc.telemetry.tracker
    tracker = AnalyticsTracker()
    
    def mock_session(*args, **kwargs):
        raise Exception("DB Error")
        
    monkeypatch.setattr(acc.telemetry.tracker, "Session", mock_session)
    
    # Should swallow error
    tracker.log_run("cmd", 10, 5)
    
    # get_json error
    res = tracker.get_json("all")
    assert "error" in res
