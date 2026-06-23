import pytest
import json
from pathlib import Path
from acc.filters.toml_loader import is_trusted, trust_file, load_filters, FilterRegistry

def test_toml_loader_trust_file(tmp_path, monkeypatch):
    from acc.filters import toml_loader
    # mock _get_trusted_file
    trusted_file = tmp_path / "trusted.json"
    monkeypatch.setattr(toml_loader, "_get_trusted_file", lambda: trusted_file)
    
    test_toml = tmp_path / "test.toml"
    test_toml.write_text("a = 1")
    
    # trust_file non-existent
    with pytest.raises(FileNotFoundError):
        trust_file(tmp_path / "nonexistent.toml")
        
    # trust_file valid
    trust_file(test_toml)
    assert is_trusted(test_toml)
    
    # is_trusted non-existent
    assert not is_trusted(tmp_path / "nonexistent.toml")
    
    # corrupt trusted.json
    trusted_file.write_text("{bad json")
    assert not is_trusted(test_toml)
    
    # trust_file with corrupt trusted.json should overwrite/fix or just rewrite
    trust_file(test_toml)
    assert is_trusted(test_toml)

def test_load_filters(tmp_path, monkeypatch):
    from acc.filters import toml_loader
    trusted_file = tmp_path / "trusted.json"
    monkeypatch.setattr(toml_loader, "_get_trusted_file", lambda: trusted_file)
    
    # non-existent
    assert load_filters(tmp_path / "nonexistent.toml") == {}
    
    test_toml = tmp_path / "test.toml"
    test_toml.write_text("invalid toml = ")
    
    # untrusted
    with pytest.raises(ValueError, match="NOT trusted"):
        load_filters(test_toml)
        
    # trust it, but invalid toml
    trust_file(test_toml)
    with pytest.raises(ValueError, match="Failed to parse TOML"):
        load_filters(test_toml)
        
    # valid toml
    test_toml.write_text('[filter.git]\ncommand = "git"\n')
    trust_file(test_toml)
    assert "filter" in load_filters(test_toml)

def test_filter_registry(tmp_path, monkeypatch):
    from acc.filters import toml_loader
    trusted_file = tmp_path / "trusted.json"
    monkeypatch.setattr(toml_loader, "_get_trusted_file", lambda: trusted_file)
    
    test_toml = tmp_path / "test.toml"
    test_toml.write_text('[filter.git]\ncommand = "git"\nstages=[]')
    trust_file(test_toml)
    
    reg = FilterRegistry()
    reg.load_from_file(test_toml)
    assert reg.get_filter("git status") is not None
    assert reg.get_filter("unknown") is None
    
    # Error loading (e.g. invalid toml) shouldn't crash load_from_file
    bad_toml = tmp_path / "bad.toml"
    bad_toml.write_text("invalid = =")
    trust_file(bad_toml)
    reg.load_from_file(bad_toml)  # should silently pass
