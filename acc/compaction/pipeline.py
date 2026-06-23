import re
import os
import tempfile
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("acc.pipeline")

class FilterPipeline:
    def __init__(self, filter_config: Dict[str, Any] = None):
        self.config = filter_config or {}
        self.stages = self.config.get("stages", [])
        self.was_truncated = False
        self.tee_path = None

    @classmethod
    def for_command(cls, command: str) -> "FilterPipeline":
        """Factory method to load the pipeline for a specific command."""
        from acc.filters.toml_loader import FilterRegistry
        from pathlib import Path
        
        registry = FilterRegistry()
        
        # In a real setup, we'd look for project local .acc/filters.toml or global
        local_toml = Path(os.getcwd()) / ".acc" / "filters.toml"
        if local_toml.exists():
            registry.load_from_file(local_toml)
            config = registry.get_filter(command)
            if config:
                return cls(config)
                
        from acc.filters.builtin import BUILTIN_FILTERS
        for k, v in BUILTIN_FILTERS.items():
            if command.startswith(k):
                return cls(v)
                
        return cls({"stages": [{"name": "strip_ansi"}]})

    def run(self, raw_output: str) -> str:
        if not raw_output:
            return ""
            
        lines = raw_output.split("\n")
        
        for stage in self.stages:
            if stage.get("enabled", True) is False:
                continue
                
            name = stage.get("name")
            if name == "strip_ansi":
                lines = self._strip_ansi(lines)
            elif name == "regex_replace":
                lines = self._regex_replace(lines, stage)
            elif name == "regex_drop":
                lines = self._regex_drop(lines, stage)
            elif name == "regex_keep":
                lines = self._regex_keep(lines, stage)
            elif name == "line_dedup":
                lines = self._line_dedup(lines)
            elif name == "smart_truncate":
                lines = self._smart_truncate(lines, stage, raw_output)
            elif name == "head_tail":
                lines = self._head_tail(lines, stage, raw_output)
            elif name == "on_empty":
                lines = self._on_empty(lines, stage)
                
        return "\n".join(lines)
        
    def _strip_ansi(self, lines: List[str]) -> List[str]:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return [ansi_escape.sub('', line) for line in lines]

    def _regex_replace(self, lines: List[str], stage: Dict[str, Any]) -> List[str]:
        pattern = stage.get("pattern")
        repl = stage.get("replacement", "")
        if not pattern:
            return lines
        try:
            regex = re.compile(pattern)
            return [regex.sub(repl, line) for line in lines]
        except re.error as e:
            logger.warning(f"Invalid regex pattern in replace: {pattern} - {e}")
            return lines

    def _regex_drop(self, lines: List[str], stage: Dict[str, Any]) -> List[str]:
        pattern = stage.get("pattern")
        if not pattern:
            return lines
        try:
            regex = re.compile(pattern)
            return [line for line in lines if not regex.search(line)]
        except re.error as e:
            logger.warning(f"Invalid regex pattern in drop: {pattern} - {e}")
            return lines

    def _regex_keep(self, lines: List[str], stage: Dict[str, Any]) -> List[str]:
        pattern = stage.get("pattern")
        if not pattern:
            return lines
        try:
            regex = re.compile(pattern)
            return [line for line in lines if regex.search(line)]
        except re.error as e:
            logger.warning(f"Invalid regex pattern in keep: {pattern} - {e}")
            return lines

    def _line_dedup(self, lines: List[str]) -> List[str]:
        seen = set()
        res = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                res.append(line)
        return res

    def _smart_truncate(self, lines: List[str], stage: Dict[str, Any], raw_output: str) -> List[str]:
        max_lines = stage.get("max_lines", 50)
        head_ratio = stage.get("head_ratio", 0.5)
        priority_pattern = stage.get("priority_lines")
        
        if len(lines) <= max_lines:
            return lines
            
        priority_regex = None
        if priority_pattern:
            try:
                priority_regex = re.compile(priority_pattern)
            except re.error as e:
                logger.warning(f"Invalid regex pattern in smart_truncate priority_lines: {priority_pattern} - {e}")
                
        head_count = int(max_lines * head_ratio)
        tail_count = max_lines - head_count
        
        # Select priority lines first
        selected = []
        if priority_regex:
            selected = [line for line in lines if priority_regex.search(line)]
            
        # If we selected too many priority lines, just use head/tail on priority lines
        if len(selected) > max_lines:
            selected = selected[:head_count] + selected[-tail_count:]
            return self._tee_truncate(selected, raw_output)
            
        # Fill the rest with head/tail from non-priority lines
        remaining_slots = max_lines - len(selected)
        if remaining_slots > 0:
            rem_head = int(remaining_slots * head_ratio)
            rem_tail = remaining_slots - rem_head
            
            non_priority = [line for line in lines if not (priority_regex and priority_regex.search(line))]
            head_lines = non_priority[:rem_head]
            tail_lines = non_priority[-rem_tail:] if rem_tail > 0 else []
            
            # Combine them: head, then priority, then tail. (Approximation of original order is hard here)
            # A better approach is to keep a mask.
            mask = [False] * len(lines)
            
            # Mark priority
            if priority_regex:
                for i, line in enumerate(lines):
                    if priority_regex.search(line):
                        mask[i] = True
            
            # Mark head and tail of what's left
            head_found = 0
            for i in range(len(lines)):
                if head_found >= rem_head:
                    break
                if not mask[i]:
                    mask[i] = True
                    head_found += 1
                    
            tail_found = 0
            for i in range(len(lines)-1, -1, -1):
                if tail_found >= rem_tail:
                    break
                if not mask[i]:
                    mask[i] = True
                    tail_found += 1
                    
            selected = [line for i, line in enumerate(lines) if mask[i]]
            
        return self._tee_truncate(selected, raw_output)

    def _head_tail(self, lines: List[str], stage: Dict[str, Any], raw_output: str) -> List[str]:
        max_lines = stage.get("max_lines", 50)
        head_ratio = stage.get("head_ratio", 0.5)
        
        if len(lines) <= max_lines:
            return lines
            
        head_count = int(max_lines * head_ratio)
        tail_count = max_lines - head_count
        
        selected = lines[:head_count] + lines[-tail_count:] if tail_count > 0 else lines[:head_count]
        return self._tee_truncate(selected, raw_output)
        
    def _on_empty(self, lines: List[str], stage: Dict[str, Any]) -> List[str]:
        fallback = stage.get("fallback", "[Empty Output]")
        if not lines or (len(lines) == 1 and not lines[0].strip()):
            return [fallback]
        return lines

    def _tee_truncate(self, selected_lines: List[str], raw_output: str) -> List[str]:
        self.was_truncated = True
        
        # Save raw output to temp file
        fd, self.tee_path = tempfile.mkstemp(prefix="acc_tee_", suffix=".log")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(raw_output)
            
        selected_lines.append(f"... [Truncated. Full output saved to {self.tee_path}]")
        return selected_lines
