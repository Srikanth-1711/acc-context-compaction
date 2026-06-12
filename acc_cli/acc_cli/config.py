from dataclasses import dataclass
from pathlib import Path

@dataclass
class AccConfig:
    max_lines: int = 400
    dedup_window: int = 5
    # later: per-command configs

def load_config() -> AccConfig:
    # TODO: load from ~/.acc/config.toml if present
    return AccConfig()
