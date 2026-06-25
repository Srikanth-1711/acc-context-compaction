import re
from typing import List, Tuple

class DeterministicCompressor:
    """Information-density-based line scoring."""
    
    # Lines that are ALWAYS kept (critical context)
    KEEP_PATTERNS = [
        r'error\[', r'ERROR', r'FAILED', r'panic', r'exception',
        r'def\s+\w+', r'class\s+\w+', r'import\s+', r'from\s+',
        r'^\s*[-*]\s',  # list items (often important)
    ]
    
    # Lines that are ALWAYS dropped (noise)
    DROP_PATTERNS = [
        r'Compiling\s+\w+', r'Finished\s+dev', r'Running\s+\d+\s+test',
        r'^\s*Downloading', r'^\s*Blocking', r'^\s*Unblocking',
        r'\d+%\s*\|', r'[#▓░]+',  # progress bars
        r'^\s*=\s*=\s*=\s*',  # pytest separators
    ]
    
    def score_line(self, line: str) -> float:
        """Score 0.0-1.0. Higher = more important."""
        if not line.strip():
            return 0.0
        
        for pattern in self.KEEP_PATTERNS:
            if re.search(pattern, line, re.I):
                return 1.0
        
        for pattern in self.DROP_PATTERNS:
            if re.search(pattern, line):
                return 0.05
        
        # Length heuristic: longer lines often have more information
        # But cap to avoid runaway
        length_score = min(len(line.strip()) / 100, 0.7)
        
        # Structural lines (indented code) score higher than flat text
        indent = len(line) - len(line.lstrip())
        indent_bonus = 0.1 if indent > 0 else 0.0
        
        return 0.3 + length_score + indent_bonus
    
    def get_drop_indices(self, text: str, target_ratio: float = 0.5) -> List[int]:
        """Returns the indices of the lines that should be dropped."""
        lines = text.split('\n')
        if len(lines) <= 10:
            return []
        
        scored: List[Tuple[int, float]] = [
            (i, self.score_line(line)) for i, line in enumerate(lines)
        ]
        
        # Sort by score descending
        scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
        
        # Take top target_ratio lines
        keep_count = max(5, int(len(lines) * target_ratio))
        # Separate mandatory keeps from scored keeps
        mandatory_keeps = {i for i, s in scored if s >= 0.9}
        scored_keeps = {i for i, _ in scored_sorted[:keep_count] if i not in mandatory_keeps}
        kept_indices = mandatory_keeps | scored_keeps
        
        # Then drop everything else
        drop_indices = [i for i, _ in scored if i not in kept_indices]
                
        return drop_indices
        
    def compress(self, text: str, target_ratio: float = 0.5) -> str:
        """
        Keep the most information-dense lines up to target_ratio.
        Preserves original order.
        """
        lines = text.split('\n')
        if len(lines) <= 10:
            return text  # Don't compress small outputs
            
        drop_indices = set(self.get_drop_indices(text, target_ratio))
        
        result = []
        dropped = 0
        for i, line in enumerate(lines):
            if i not in drop_indices:
                if dropped > 0:
                    result.append(f"... [{dropped} lines dropped] ...")
                    dropped = 0
                result.append(line)
            else:
                dropped += 1
        
        if dropped > 0:
            result.append(f"... [{dropped} lines dropped] ...")
        
        return '\n'.join(result)
    
    def run(self, text: str) -> str:
        return self.compress(text)
