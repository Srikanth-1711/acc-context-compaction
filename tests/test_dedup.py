import pytest
import os
import tempfile
from acc.compaction.dedup import DedupCache

@pytest.fixture(autouse=True)
def clean_temp_files():
    # Cleanup before and after tests
    def _cleanup():
        for session_id in ["test-collision", "test-session", "different-session"]:
            path = os.path.join(tempfile.gettempdir(), f"acc_dedup_{session_id}.json")
            if os.path.exists(path):
                os.remove(path)
    _cleanup()
    yield
    _cleanup()

def test_dedup_cache_collision():
    cache = DedupCache("test-collision")
    cache.next_turn()  # turn 1
    
    text = "A" * 1000
    # First check adds to cache, returns None
    assert cache.check(text) is None
    
    # Second check hits cache
    res = cache.check(text)
    assert res is not None
    assert "[Output identical to turn #1]" in res
    
    # Different text returns None
    text2 = "B" * 1000
    assert cache.check(text2) is None

def test_dedup_persistence():
    cache1 = DedupCache(session_id="test-session")
    cache1.next_turn()  # turn 1
    
    cache1.check("Persistent string")
    
    cache2 = DedupCache(session_id="test-session")
    res = cache2.check("Persistent string")
    assert res is not None
    assert "[Output identical to turn #1]" in res
    
    cache3 = DedupCache(session_id="different-session")
    assert cache3.check("Persistent string") is None

def test_dedup_load_corrupted(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    from acc.compaction.dedup import DedupCache
    
    corrupt_file = tmp_path / "acc_dedup_corrupt_session.json"
    corrupt_file.write_text("{bad json")
    
    cache = DedupCache("corrupt_session")
    assert cache.turn == 0
    assert cache.fingerprints == {}

def test_dedup_save_oserror(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    from acc.compaction.dedup import DedupCache
    
    cache = DedupCache("oserror_session")
    
    import builtins
    original_open = builtins.open
    def mock_open(file, mode='r', **kwargs):
        if mode == 'w' and "oserror_session" in str(file):
            raise OSError("Disk full")
        return original_open(file, mode, **kwargs)
        
    monkeypatch.setattr(builtins, "open", mock_open)
    
    # Should swallow OSError
    cache._save()
