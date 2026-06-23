import pytest
import tempfile
import os
import builtins
from acc.mcp_server import acc_run

def test_acc_run_session_fallback(monkeypatch):
    import acc.mcp_server as mcp_server
    
    class MockCache:
        def __init__(self, session_id):
            self.session_id = session_id
        def next_turn(self): pass
        def check(self, text): return None

    from acc.compaction.executor import ExecutionResult
    def mock_exec(cmd_list, **kwargs):
        return ExecutionResult(stdout="hello", exit_code=0)
    
    passed_sessions = []
    def track_cache(sid):
        passed_sessions.append(sid)
        return MockCache(sid)
        
    monkeypatch.setattr(mcp_server, "get_session_cache", track_cache)
    monkeypatch.setattr(mcp_server, "execute_command", mock_exec)
    monkeypatch.setattr(mcp_server, "Session", lambda *args, **kwargs: __import__('contextlib').nullcontext())
    
    # Create dummy MemoryRetriever to not crash
    class MockRetriever:
        def __init__(self, *args, **kwargs): pass
        def temporal_query(self, *args, **kwargs): return []
    monkeypatch.setattr(mcp_server, "MemoryRetriever", MockRetriever)

    # explicit
    acc_run("cmd", session_id="explicit")
    assert passed_sessions[-1] == "explicit"
    
    # context
    acc_run("cmd", context={"session_id": "ctx-session"})
    assert passed_sessions[-1] == "ctx-session"
    
    # default
    acc_run("cmd")
    assert passed_sessions[-1] == "default"

def test_acc_run_dedup(monkeypatch):
    import acc.mcp_server as mcp_server
    class MockCache:
        def next_turn(self): pass
        def check(self, text): return "[Output identical to turn #1] abc"

    from acc.compaction.executor import ExecutionResult
    def mock_exec(cmd_list, **kwargs):
        return ExecutionResult(stdout="hello", exit_code=0)
    
    monkeypatch.setattr(mcp_server, "get_session_cache", lambda sid: MockCache())
    monkeypatch.setattr(mcp_server, "execute_command", mock_exec)
    
    res = acc_run("cmd")
    assert "[Output identical to turn #1]" in res["output"]
    assert res["deduped"] is True

def test_acc_run_errors(monkeypatch):
    import acc.mcp_server as mcp_server
    class MockCache:
        def next_turn(self): pass
        def check(self, text): return None

    from acc.compaction.executor import ExecutionResult
    def mock_exec(cmd_list, **kwargs):
        return ExecutionResult(stdout="", exit_code=1, error="mock error")
    
    monkeypatch.setattr(mcp_server, "get_session_cache", lambda sid: MockCache())
    monkeypatch.setattr(mcp_server, "execute_command", mock_exec)
    
    res = acc_run("cmd")
    assert "mock error" in res["output"] # The error might be part of output
