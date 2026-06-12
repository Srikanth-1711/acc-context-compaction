from typing import Callable, List, Dict, Any
from acc.filters.strip_ansi import strip_ansi
from acc.filters.dedup import dedup
from acc.filters.noise import remove_noise
from acc.filters.head_tail import head_tail
from acc.structured.python_ast import compress_python
from acc.structured.json_minifier import compress_json

class FilterPipeline:
    def __init__(self, profile: Dict[str, Any] = None):
        self.profile = profile or {}
        
    def execute(self, text: str) -> str:
        if not text:
            return ""
            
        profile_type = self.profile.get("type", "text")
        
        # If language-aware, do structured compression first
        if profile_type == "python":
            text = compress_python(text)
        elif profile_type == "json":
            text = compress_json(text, max_depth=2)
        elif profile_type == "conversation":
            from acc.structured.conversation import compress_conversation
            backend = self.profile.get("backend", "heuristic")
            text = compress_conversation(text, backend=backend)
            
        lines = text.split("\n")
        
        # 1. Strip ANSI
        lines = strip_ansi(lines)
        
        # 2. Dedup
        lines = dedup(lines)
        
        # 3. Noise Removal (use custom patterns if provided)
        noise_patterns = self.profile.get("noise_patterns", None)
        lines = remove_noise(lines, custom_patterns=noise_patterns)
        
        # 4. Head/Tail
        max_lines = self.profile.get("max_lines", 2000)
        head_ratio = self.profile.get("head_ratio", 0.2)
        pre_ht_len = len(lines)
        lines = head_tail(lines, max_lines=max_lines, head_ratio=head_ratio)
        
        if len(lines) < pre_ht_len:
            import time
            import os
            import tempfile
            ts = int(time.time())
            tmp_dir = tempfile.gettempdir()
            log_path = os.path.join(tmp_dir, f"acc_tee_{ts}.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(text)
            lines.append(f"\\n... [Truncated to save tokens. Full raw output saved to {log_path}. Use view_file to read if necessary.]")
            
        return "\n".join(lines)
