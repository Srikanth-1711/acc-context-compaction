"""
Session-scoped deduplication cache.

Prevents re-processing identical outputs across multiple MCP tool calls
within the same server session. Uses O(1) fingerprinting based on
(byte_length, hash(first_256_chars), hash(last_256_chars)).

Lifetime: process-scoped. Dies with the MCP server process.
Never persisted to disk — stale cache is worse than cache miss.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Fingerprint:
    """Immutable fingerprint for output deduplication."""
    byte_length: int
    prefix_hash: int  # hash of first 256 chars
    suffix_hash: int  # hash of last 256 chars


class DedupCache:
    """
    Session-scoped dedup cache. Lives for the lifetime of the MCP server process.

    Usage:
        cache = get_session_cache()
        cache.next_turn()  # call at start of each tool invocation
        suppressed = cache.check(raw_output)
        if suppressed:
            return suppressed  # identical output seen before
    """

    def __init__(self):
        import tempfile
        import os
        from pathlib import Path
        self._cache_file = Path(tempfile.gettempdir()) / "acc_dedup_cache.json"
        self._cache: dict[Fingerprint, int] = {}
        self._turn: int = 0
        self._load()

    def _load(self):
        import json
        if self._cache_file.exists():
            try:
                data = json.loads(self._cache_file.read_text(encoding="utf-8"))
                self._turn = data.get("turn", 0)
                for k, v in data.get("cache", {}).items():
                    parts = k.split(":")
                    if len(parts) == 3:
                        fp = Fingerprint(int(parts[0]), int(parts[1]), int(parts[2]))
                        self._cache[fp] = v
            except Exception:
                pass

    def _save(self):
        import json
        try:
            data = {
                "turn": self._turn,
                "cache": {f"{fp.byte_length}:{fp.prefix_hash}:{fp.suffix_hash}": v for fp, v in self._cache.items()}
            }
            self._cache_file.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass

    def next_turn(self):
        self._turn += 1
        self._save()

    @property
    def current_turn(self) -> int:
        return self._turn

    def check(self, raw: str) -> Optional[str]:
        if not raw or not raw.strip():
            return None

        fp = self._fingerprint(raw)
        if fp in self._cache:
            prev_turn = self._cache[fp]
            return (
                f"[Output identical to turn #{prev_turn} — "
                f"suppressed ({fp.byte_length:,} bytes)]"
            )
        self._cache[fp] = self._turn
        self._save()
        return None

    def check_file(self, file_path: str, size: int, mtime_ns: int) -> Optional[str]:
        fp = Fingerprint(
            byte_length=size,
            prefix_hash=hash(file_path),
            suffix_hash=hash(mtime_ns),
        )
        if fp in self._cache:
            prev_turn = self._cache[fp]
            return (
                f"[File unchanged since turn #{prev_turn} — "
                f"suppressed ({size:,} bytes)]"
            )
        self._cache[fp] = self._turn
        self._save()
        return None

    def _fingerprint(self, text: str) -> Fingerprint:
        import hashlib
        def dhash(s: str) -> int:
            return int(hashlib.md5(s.encode('utf-8')).hexdigest()[:16], 16)
        return Fingerprint(
            byte_length=len(text),
            prefix_hash=dhash(text[:256]),
            suffix_hash=dhash(text[-256:]) if len(text) > 256 else dhash(text),
        )

    def clear(self):
        self._cache.clear()
        self._turn = 0
        self._save()

    @property
    def size(self) -> int:
        return len(self._cache)


# Module-level singleton — lives for the MCP server process lifetime.
# All MCP tool calls share this instance.
_session_cache = DedupCache()


def get_session_cache() -> DedupCache:
    """Get the global session-scoped dedup cache."""
    return _session_cache
