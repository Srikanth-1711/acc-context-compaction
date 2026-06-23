import tomli
import hashlib
import json
import os
from pathlib import Path
import tempfile
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("acc.toml_loader")

def _get_trusted_file() -> Path:
    trusted_dir = Path.home() / ".acc"
    trusted_dir.mkdir(parents=True, exist_ok=True)
    return trusted_dir / "trusted.json"

def _hash_file(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def is_trusted(filepath: Path) -> bool:
    """Check if the TOML file hash matches the trusted hash."""
    if not filepath.exists():
        return False
    
    trusted_file = _get_trusted_file()
    if not trusted_file.exists():
        return False
        
    try:
        trusted_hashes = json.loads(trusted_file.read_text(encoding='utf-8'))
        current_hash = _hash_file(filepath)
        return trusted_hashes.get(str(filepath.absolute())) == current_hash
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to read trusted hashes: {e}")
        return False

def trust_file(filepath: Path):
    """Trust the TOML file by storing its hash."""
    if not filepath.exists():
        raise FileNotFoundError(f"Cannot trust non-existent file: {filepath}")
        
    trusted_file = _get_trusted_file()
    trusted_hashes = {}
    if trusted_file.exists():
        try:
            trusted_hashes = json.loads(trusted_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to read trusted hashes: {e}")
            
    trusted_hashes[str(filepath.absolute())] = _hash_file(filepath)
    
    fd, temp_path = tempfile.mkstemp(dir=trusted_file.parent)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(trusted_hashes, f, indent=2)
    os.replace(temp_path, trusted_file)

def load_filters(filepath: Path) -> Dict[str, Any]:
    """Loads a TOML filters config if trusted, else raises ValueError."""
    if not filepath.exists():
        return {}
        
    if not is_trusted(filepath):
        # Allow loading if the user wants to test, but we should warn or raise.
        # Following declarative trust model, we raise an error.
        raise ValueError(f"Filter config at {filepath} is NOT trusted. Run `acc trust` to verify.")
        
    try:
        with open(filepath, "rb") as f:
            return tomli.load(f)
    except tomli.TOMLDecodeError as e:
        raise ValueError(f"Failed to parse TOML file at {filepath}: {e}")

class FilterRegistry:
    def __init__(self):
        self.filters: Dict[str, Any] = {}
        
    def load_from_file(self, filepath: Path):
        try:
            config = load_filters(filepath)
            filters_dict = config.get("filter", {})
            for key, filter_def in filters_dict.items():
                cmd_key = filter_def.get("command", key)
                self.filters[cmd_key] = filter_def
        except Exception as e:
            logger.error(f"Failed to load filters from {filepath}: {e}")

    def get_filter(self, command: str) -> Optional[Dict[str, Any]]:
        # Naive matching: if command starts with the filter's command, we use it
        # E.g. command "cargo test --quiet" matches "cargo test"
        for k, v in self.filters.items():
            if command.startswith(k):
                return v
        return None
