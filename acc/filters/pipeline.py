from typing import Callable, List
from acc.filters.strip_ansi import strip_ansi
from acc.filters.dedup import dedup
from acc.filters.noise import remove_noise
from acc.filters.head_tail import head_tail

class FilterPipeline:
    def __init__(self, filters: List[Callable[[List[str]], List[str]]] = None):
        if filters is None:
            # Default deterministic RTK pipeline
            self.filters = [
                strip_ansi,
                dedup,
                remove_noise,
                lambda lines: head_tail(lines, max_lines=2000, head_ratio=0.2)
            ]
        else:
            self.filters = filters
            
    def execute(self, text: str) -> str:
        if not text:
            return ""
            
        lines = text.split("\n")
        
        for f in self.filters:
            lines = f(lines)
            
        return "\n".join(lines)
