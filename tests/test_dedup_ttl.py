import pytest
import time
from acc.compaction.dedup import DedupCache, CACHE_TTL_SECONDS, MAX_CACHE_ENTRIES

def test_dedup_ttl_eviction(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    cache = DedupCache("ttl_session")
    
    # Add an entry
    cache.check("Test string 1")
    fp1 = list(cache.fingerprints.keys())[0]
    
    # Manually backdate the timestamp to beyond TTL
    cache.fingerprints[fp1]['timestamp'] = time.time() - CACHE_TTL_SECONDS - 100
    cache._save()
    
    # Reload cache, the entry should be evicted
    cache2 = DedupCache("ttl_session")
    assert fp1 not in cache2.fingerprints

def test_dedup_lru_eviction(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    
    # Temporarily lower MAX_CACHE_ENTRIES for test
    import acc.compaction.dedup
    monkeypatch.setattr(acc.compaction.dedup, "MAX_CACHE_ENTRIES", 2)
    
    cache = DedupCache("lru_session")
    
    cache.check("String A")
    time.sleep(0.01)
    cache.check("String B")
    time.sleep(0.01)
    cache.check("String C")
    
    # Cache should only have B and C
    assert len(cache.fingerprints) == 2
    
    # String A should be a miss (evicted)
    assert cache.check("String A") is None
