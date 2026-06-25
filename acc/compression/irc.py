import base64
import zlib
import re
import os
import tempfile
import uuid
import json
import logging
from typing import List

logger = logging.getLogger("acc.irc")

class InlineReversibleCompressor:
    """
    Compresses text by replacing dropped lines with a recovery token.
    The token contains zlib-compressed original lines + metadata.
    The LLM sees: "[...3 lines compressed: irc:abc123...]"
    When the LLM asks to expand, decode the token and restore.
    """
    
    TOKEN_PREFIX = "irc:"
    REF_PREFIX = "ircref:"
    
    def __init__(self):
        self.storage_dir = os.path.join(tempfile.gettempdir(), "acc_irc_storage")
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _external_store(self, token: str, kept_lines: List[str], dropped_count: int) -> str:
        ref_id = str(uuid.uuid4())
        filepath = os.path.join(self.storage_dir, f"{ref_id}.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(token)
            
        marker = f"[...{dropped_count} lines compressed: {self.REF_PREFIX}{ref_id}...]"
        return '\n'.join(kept_lines + [marker])
        
    def _external_load(self, ref_id: str) -> str:
        filepath = os.path.join(self.storage_dir, f"{ref_id}.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def compress(self, text: str, drop_indices: List[int]) -> str:
        """Replace dropped lines with inline recovery token."""
        if not drop_indices:
            return text
            
        lines = text.split('\n')
        drop_set = set(drop_indices)
        
        dropped = [lines[i] for i in sorted(drop_set)]
        kept = [lines[i] for i in range(len(lines)) if i not in drop_set]
        
        # Compress dropped lines
        payload = json.dumps({'indices': sorted(drop_set), 'lines': dropped}).encode('utf-8')
        compressed = zlib.compress(payload, level=9)
        token = base64.urlsafe_b64encode(compressed).decode('ascii')
        
        # Truncate token if too long (fall back to external storage)
        if len(token) > 200:
            return self._external_store(token, kept, len(dropped))
        
        marker = f"[...{len(dropped)} lines compressed: {self.TOKEN_PREFIX}{token}...]"
        return '\n'.join(kept + [marker])
    
    def expand(self, compressed_text: str) -> str:
        """Recover original from inline token."""
        # Find the marker
        match = re.search(r'\[\.\.\.\d+ lines compressed: (irc:|ircref:)([a-zA-Z0-9_\-]+)\.\.\.\]', compressed_text)
        if not match:
            return compressed_text
            
        prefix = match.group(1)
        token_or_ref = match.group(2)
        
        if prefix == self.REF_PREFIX:
            token = self._external_load(token_or_ref)
        else:
            token = token_or_ref
            
        if not token:
            return compressed_text  # Cannot recover
            
        try:
            compressed = base64.urlsafe_b64decode(token)
            payload_json = zlib.decompress(compressed).decode('utf-8')
            payload = json.loads(payload_json)
            
            drop_indices = payload['indices']
            dropped_lines = payload['lines']
            
            # Remove the marker line from the kept lines
            lines = compressed_text.split('\n')
            kept = [line for line in lines if not re.match(r'^\[\.\.\.\d+ lines compressed:', line)]
            
            drop_indices_set = set(drop_indices)
            
            result = []
            kept_idx = 0
            for i in range(len(kept) + len(drop_indices)):
                if i in drop_indices_set:
                    # Find which dropped line this corresponds to
                    # Since drop_indices is sorted, we can use index()
                    result.append(dropped_lines[drop_indices.index(i)])
                else:
                    if kept_idx < len(kept):
                        result.append(kept[kept_idx])
                        kept_idx += 1
                        
            return '\n'.join(result)
        except Exception as e:
            logger.error(f"IRC expand failed: {e}")
            return compressed_text
