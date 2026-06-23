import hashlib
import json
import tempfile
import os
import logging

logger = logging.getLogger("acc.dedup")

class DedupCache:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.fingerprints = {}  # Map fingerprint to turn number
        self.turn = 0
        self.file_path = os.path.join(tempfile.gettempdir(), f"acc_dedup_{session_id}.json")
        self._load()
        
    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.fingerprints = data.get('fingerprints', {})
                    self.turn = data.get('turn', 0)
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Failed to load dedup cache from {self.file_path}: {e}")
                self.fingerprints = {}
                self.turn = 0

    def _save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({'fingerprints': self.fingerprints, 'turn': self.turn}, f)
        except OSError as e:
            logger.error(f"Failed to save dedup cache to {self.file_path}: {e}")

    def _fingerprint(self, text: str) -> str:
        """Triple hash fingerprint: (length, md5(first256), md5(last256))"""
        length = len(text)
        if length == 0:
            return "0:d41d8cd98f00b204e9800998ecf8427e:d41d8cd98f00b204e9800998ecf8427e"
        
        first_chunk = text[:256].encode('utf-8')
        last_chunk = text[-256:].encode('utf-8')
        
        h1 = hashlib.md5(first_chunk).hexdigest()
        h2 = hashlib.md5(last_chunk).hexdigest()
        
        return f"{length}:{h1}:{h2}"

    def check(self, text: str) -> str:
        """Returns the deduplicated response if seen before, else adds to cache and returns None."""
        fp = self._fingerprint(text)
        if fp in self.fingerprints:
            turn_seen = self.fingerprints[fp]
            return f"[Output identical to turn #{turn_seen}] Fingerprint: {fp}"
            
        self.fingerprints[fp] = self.turn
        self._save()
        return None
        
    def next_turn(self):
        self.turn += 1
        self._save()

def get_session_cache(session_id: str) -> DedupCache:
    return DedupCache(session_id)
