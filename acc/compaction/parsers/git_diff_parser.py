"""Parser for git diff, git show output."""

import re
from acc.compaction.parsers.base import BaseParser

# Patterns for whitespace-only and comment-only changes
_COMMENT_PREFIXES = ("#", "//", "/*", " *", "*/", "*", "<!--", "-->")
_CRITICAL_KEYWORDS = (
    "lock", "mutex", "semaphore", "atomic",
    "interrupt", "signal", "critical_section",
    "synchronized", "volatile", "unsafe",
)


class GitDiffParser(BaseParser):
    tool_names = ["git"]

    def can_handle(self, command: str) -> bool:
        # Only handle git diff and git show, not other git commands
        # The command string from compaction_service is just the base command "git"
        # We need broader matching — we'll handle it and detect subcommand from output
        cmd_lower = command.lower()
        if cmd_lower.endswith(".exe"):
            cmd_lower = cmd_lower[:-4]
        cmd_lower = cmd_lower.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        return cmd_lower == "git"

    def parse(self, raw_output: str, **kwargs) -> str:
        try:
            return self._parse_impl(raw_output, **kwargs)
        except Exception as e:
            return self.fallback(raw_output, reason=str(e))

    def _parse_impl(self, raw_output: str, **kwargs) -> str:
        lines = raw_output.split("\n")

        # Detect if this is diff output
        has_diff = any(l.startswith("diff --git") for l in lines[:50])
        if has_diff:
            return self._parse_diff(lines)
            
        # Detect if this is status output
        is_status = any(
            "On branch " in l or 
            "Changes to be committed:" in l or 
            "Untracked files:" in l or 
            l.startswith("? ") or 
            l.startswith("1 ") or 
            l.startswith("M ") or 
            l.startswith(" D ") or
            l.startswith("?? ")
            for l in lines[:15]
        )
        if is_status:
            return self._parse_status(lines, **kwargs)

        # Not recognized — return raw for the generic pipeline to handle
        return raw_output

    def _parse_status(self, lines: list[str], **kwargs) -> str:
        modified = set()
        untracked = set()
        deleted = set()
        staged = set()
        
        mode = "normal"
        for line in lines:
            stripped = line.strip()
            if not stripped: continue
            
            # Track sections in standard output
            if "Changes to be committed:" in line: mode = "staged"
            elif "Changes not staged for commit:" in line: mode = "unstaged"
            elif "Untracked files:" in line: mode = "untracked"
            elif "On branch " in line: mode = "normal"
            
            # Porcelain v2
            if line.startswith("1 ") or line.startswith("2 "):
                parts = line.split()
                if len(parts) >= 9:
                    status_code = parts[1]
                    path = parts[-1]
                    if self._is_noise_file(path): continue
                    if "D" in status_code: deleted.add(path)
                    elif "A" in status_code: staged.add(path)
                    elif "M" in status_code: modified.add(path)
                continue
            if line.startswith("? "):
                path = line.split(" ", 1)[1]
                if not self._is_noise_file(path): untracked.add(path)
                continue
                
            # Porcelain v1
            if len(line) >= 3 and line[2] == " " and not line.startswith("  ") and mode == "normal":
                st = line[:2]
                path = line[3:]
                if self._is_noise_file(path): continue
                if "??" in st: untracked.add(path)
                elif "D" in st: deleted.add(path)
                elif "A" in st: staged.add(path)
                elif "M" in st: modified.add(path)
                continue
                
            # Standard output
            if stripped.startswith("modified:"):
                path = stripped.split(":", 1)[1].strip()
                if self._is_noise_file(path): continue
                if mode == "staged": staged.add(path)
                else: modified.add(path)
            elif stripped.startswith("deleted:"):
                path = stripped.split(":", 1)[1].strip()
                if self._is_noise_file(path): continue
                deleted.add(path)
            elif stripped.startswith("new file:"):
                path = stripped.split(":", 1)[1].strip()
                if self._is_noise_file(path): continue
                staged.add(path)
            elif mode == "untracked" and not stripped.startswith("(") and not stripped.endswith(":"):
                # Usually untracked files are indented
                if line.startswith("\t") or line.startswith("  "):
                    if not self._is_noise_file(stripped): untracked.add(stripped)

        # Build output
        out = []
        counts = []
        if modified: counts.append(f"{len(modified)} modified")
        if untracked: counts.append(f"{len(untracked)} untracked")
        if deleted: counts.append(f"{len(deleted)} deleted")
        if staged: counts.append(f"{len(staged)} staged")
        
        if not counts:
            return "[STATUS] Clean working tree"
            
        out.append(f"[STATUS] {', '.join(counts)}")
        
        verbosity = kwargs.get("verbosity", "compact")
        
        def _fmt(files_set):
            files = sorted(files_set)
            if verbosity != "full" and len(files) > 1:
                return f"{files[0]} ... (+{len(files)-1} more)"
            return ", ".join(files)
            
        if modified: out.append(f"Modified: {_fmt(modified)}")
        if staged: out.append(f"Staged: {_fmt(staged)}")
        if untracked: out.append(f"Untracked: {_fmt(untracked)}")
        if deleted: out.append(f"Deleted: {_fmt(deleted)}")
        
        return "\n".join(out)

    def _is_noise_file(self, path: str) -> bool:
        path = path.lower()
        if "__pycache__" in path or ".pytest_cache" in path or ".cursor" in path:
            return True
        if path.endswith(".pyc") or path.endswith(".pyo"):
            return True
        return False

    def _parse_diff(self, lines: list[str]) -> str:
        files = []
        current_file = None
        current_hunks = []
        total_raw_lines = 0
        total_shown_lines = 0
        total_whitespace_skipped = 0
        total_comment_skipped = 0
        critical_changes = 0

        for line in lines:
            if line.startswith("diff --git"):
                # Flush previous file
                if current_file:
                    files.append(self._flush_file(
                        current_file, current_hunks,
                    ))
                # Parse file path
                parts = line.split(" b/", 1)
                current_file = parts[1] if len(parts) > 1 else line
                current_hunks = []
                continue

            if current_file is None:
                continue

            # Skip metadata lines
            if line.startswith("index ") or line.startswith("--- ") or line.startswith("+++ "):
                continue
            if line.startswith("old mode") or line.startswith("new mode"):
                continue

            # Hunk header
            if line.startswith("@@ "):
                current_hunks.append({"header": line, "changes": [], "is_whitespace": True, "is_comment": True, "is_critical": False})
                continue

            # Change lines within a hunk
            if current_hunks and (line.startswith("+") or line.startswith("-")):
                content = line[1:].strip()
                total_raw_lines += 1

                hunk = current_hunks[-1]
                hunk["changes"].append(line)

                # Check if this change is substantive
                if content:  # Non-empty after stripping
                    hunk["is_whitespace"] = False

                    if not any(content.startswith(p) for p in _COMMENT_PREFIXES):
                        hunk["is_comment"] = False

                    # Check for critical patterns
                    content_lower = content.lower()
                    if any(kw in content_lower for kw in _CRITICAL_KEYWORDS):
                        hunk["is_critical"] = True

            elif current_hunks and line.startswith(" "):
                # Context line
                if current_hunks[-1]["changes"]:
                    current_hunks[-1]["changes"].append(line)

        # Flush last file
        if current_file:
            files.append(self._flush_file(current_file, current_hunks))

        # Build summary output
        result = []
        for f in files:
            total_shown_lines += f["shown"]
            total_whitespace_skipped += f["ws_skipped"]
            total_comment_skipped += f["comment_skipped"]
            critical_changes += f["critical_count"]

            header = f"[DIFF] {f['name']}: {f['raw']} lines → {f['shown']} shown"
            skips = []
            if f["ws_skipped"] > 0:
                skips.append(f"{f['ws_skipped']} whitespace")
            if f["comment_skipped"] > 0:
                skips.append(f"{f['comment_skipped']} comments")
            if skips:
                header += f" ({', '.join(skips)} skipped)"
            if f["critical_count"] > 0:
                header += f" [{f['critical_count']} CRITICAL]"
            result.append(header)

            for hunk_out in f["hunk_outputs"]:
                result.append(hunk_out)

        if not result:
            return "[DIFF] No changes"

        return "\n".join(result)

    def _flush_file(self, filename: str, hunks: list[dict]) -> dict:
        raw_count = 0
        shown_count = 0
        ws_skipped = 0
        comment_skipped = 0
        critical_count = 0
        hunk_outputs = []

        for hunk in hunks:
            change_count = len([c for c in hunk["changes"] if c.startswith("+") or c.startswith("-")])
            raw_count += change_count

            if hunk["is_critical"]:
                # Always include critical hunks in full
                critical_count += 1
                hunk_outputs.append(f"  [CRITICAL] {hunk['header']}")
                for c in hunk["changes"]:
                    hunk_outputs.append(f"  {c}")
                    shown_count += 1
            elif hunk["is_whitespace"]:
                ws_skipped += change_count
            elif hunk["is_comment"]:
                comment_skipped += change_count
            else:
                # Normal hunk — include
                hunk_outputs.append(f"  {hunk['header']}")
                for c in hunk["changes"]:
                    hunk_outputs.append(f"  {c}")
                    shown_count += 1

        return {
            "name": filename,
            "raw": raw_count,
            "shown": shown_count,
            "ws_skipped": ws_skipped,
            "comment_skipped": comment_skipped,
            "critical_count": critical_count,
            "hunk_outputs": hunk_outputs,
        }
