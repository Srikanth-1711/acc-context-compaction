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
        self._cache: dict[Fingerprint, int] = {}  # fingerprint → turn number
        self._turn: int = 0

    def next_turn(self):
        """Increment turn counter. Call at the start of each tool invocation."""
        self._turn += 1

    @property
    def current_turn(self) -> int:
        return self._turn

    def check(self, raw: str) -> Optional[str]:
        """
        Check if this output was seen before in this session.

        Returns a suppression message if output was seen before, None otherwise.
        On first seeing an output, it is fingerprinted and cached.
        """
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
        return None

    def check_file(self, file_path: str, size: int, mtime_ns: int) -> Optional[str]:
        """
        Check if a file has been read before based on stat metadata.
        O(1) — does not require reading the file contents.

        Returns a suppression message if the file was read with
        identical size and mtime, None otherwise.
        """
        # Use a synthetic fingerprint from file metadata
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
        return None

    def _fingerprint(self, text: str) -> Fingerprint:
        """Create an O(1) fingerprint from text content."""
        return Fingerprint(
            byte_length=len(text),
            prefix_hash=hash(text[:256]),
            suffix_hash=hash(text[-256:]) if len(text) > 256 else hash(text),
        )

    def clear(self):
        """Reset the cache. Called on session end."""
        self._cache.clear()
        self._turn = 0

    @property
    def size(self) -> int:
        """Number of entries in the cache."""
        return len(self._cache)


# Module-level singleton — lives for the MCP server process lifetime.
# All MCP tool calls share this instance.
_session_cache = DedupCache()


def get_session_cache() -> DedupCache:
    """Get the global session-scoped dedup cache."""
    return _session_cache
