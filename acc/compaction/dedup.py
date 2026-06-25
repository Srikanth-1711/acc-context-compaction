import hashlib
import json
import tempfile
import os
import logging
import time

logger = logging.getLogger("acc.dedup")

MAX_CACHE_ENTRIES = 10000
CACHE_TTL_SECONDS = 86400 * 7  # 7 days

class DedupCache:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.fingerprints = {}  # Map fingerprint to data dict
        self.turn = 0
        self.file_path = os.path.join(tempfile.gettempdir(), f"acc_dedup_{session_id}.json")
        self._load()
        
    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    now = time.time()
                    
                    # Convert old format to new format if needed
                    raw_fps = data.get('fingerprints', {})
                    valid_fps = {}
                    
                    for k, v in raw_fps.items():
                        if isinstance(v, int):
                            # Old format: just the turn number
                            valid_fps[k] = {'turn': v, 'timestamp': now}
                        elif isinstance(v, dict):
                            # New format
                            timestamp = v.get('timestamp', 0)
                            if now - timestamp < CACHE_TTL_SECONDS:
                                valid_fps[k] = v
                    
                    self.fingerprints = valid_fps
                    
                    # Enforce max size: keep most recent
                    if len(self.fingerprints) > MAX_CACHE_ENTRIES:
                        sorted_items = sorted(
                            self.fingerprints.items(),
                            key=lambda x: x[1].get('timestamp', 0),
                            reverse=True
                        )
                        self.fingerprints = dict(sorted_items[:MAX_CACHE_ENTRIES])
                        
                    self.turn = data.get('turn', 0)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load dedup cache from {self.file_path}: {e}")
                self.fingerprints = {}
                self.turn = 0

    def _save(self):
        try:
            with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(self.file_path), delete=False, encoding='utf-8') as tmp:
                json.dump({'fingerprints': self.fingerprints, 'turn': self.turn}, tmp)
            os.replace(tmp.name, self.file_path)
        except OSError as e:
            logger.error(f"Failed to save dedup cache to {self.file_path}: {e}")
            if 'tmp' in locals() and os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass

    def _fingerprint(self, text: str) -> str:
        """Full SHA-256 of content, not just boundaries."""
        if not text:
            return "sha256:" + hashlib.sha256(b"").hexdigest()
        
        # Hash full content + length as sanity check
        full_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"sha256:{len(text)}:{full_hash}"

    def check(self, text: str) -> str:
        """Returns the deduplicated response if seen before, else adds to cache and returns None."""
        fp = self._fingerprint(text)
        if fp in self.fingerprints:
            turn_seen = self.fingerprints[fp].get('turn', 0)
            # Update timestamp on hit
            self.fingerprints[fp]['timestamp'] = time.time()
            self._save()
            return f"[Output identical to turn #{turn_seen}] Fingerprint: {fp}"
            
        self.fingerprints[fp] = {'turn': self.turn, 'timestamp': time.time()}
        
        # Enforce max size on add
        if len(self.fingerprints) > MAX_CACHE_ENTRIES:
            sorted_items = sorted(
                self.fingerprints.items(),
                key=lambda x: x[1].get('timestamp', 0),
                reverse=True
            )
            self.fingerprints = dict(sorted_items[:MAX_CACHE_ENTRIES])
            
        self._save()
        return None
        
    def next_turn(self):
        self.turn += 1
        self._save()

def get_session_cache(session_id: str) -> DedupCache:
    return DedupCache(session_id)
