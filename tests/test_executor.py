import pytest
import subprocess
from acc.compaction.executor import execute_command

def test_execute_success():
    result = execute_command(["python", "-c", "print('hello world')"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello world"
    assert not result.error

def test_execute_command_not_found():
    result = execute_command(["nonexistent_command_12345"])
    assert result.exit_code == 127
    assert "[Command not found" in result.error

def test_execute_timeout(monkeypatch):
    # Instead of actually sleeping, we can mock Popen.communicate to raise TimeoutExpired
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self.returncode = None
        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=timeout)
        def kill(self):
            pass
        def wait(self):
            self.returncode = -1

    monkeypatch.setattr(subprocess, "Popen", MockPopen)
    
    result = execute_command(["fake", "cmd"], timeout=1)
    assert result.exit_code == -1
    assert "[Command timed out after 1s]" in result.error

def test_execute_truncation(monkeypatch):
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self.returncode = 0
        def communicate(self, timeout=None):
            return ("A" * 200, None)
        
    monkeypatch.setattr(subprocess, "Popen", MockPopen)
    
    result = execute_command(["fake"], max_output_bytes=100)
    assert result.truncated is True
    assert "[ACC FATAL: Output exceeded 10MiB hard limit. Truncated.]" in result.stdout
    assert result.stdout.startswith("A" * 100)

def test_executor_errors(monkeypatch):
    # Empty command
    res = execute_command([])
    assert res.exit_code == 1
    assert "empty" in res.error.lower()
    
    # PermissionError
    def mock_popen_perm(*args, **kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(subprocess, "Popen", mock_popen_perm)
    res = execute_command(["cmd"])
    assert res.exit_code == 126
    assert "denied" in res.error.lower()
    
    # OSError
    def mock_popen_os(*args, **kwargs):
        raise OSError("os error")
    monkeypatch.setattr(subprocess, "Popen", mock_popen_os)
    res = execute_command(["cmd"])
    assert res.exit_code == 1
    assert "os error" in res.error.lower()
