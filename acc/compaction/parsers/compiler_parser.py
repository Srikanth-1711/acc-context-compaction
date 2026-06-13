"""Parser for compiler output: gcc, g++, clang, clang++, cross-compilers."""

import json
import re
from acc.compaction.parsers.base import BaseParser

# Matches: file:line:col: severity: message
_GCC_DIAG_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s+(error|warning|fatal error):\s+(.+)$"
)

# Lines to drop entirely
_DROP_PREFIXES = (
    "In file included from",
    "                 from",
    "In member function",
    "In function",
    "In instantiation of",
    "   required from",
    "   required by",
)


class CompilerParser(BaseParser):
    tool_names = [
        "gcc", "g++", "cc", "c++",
        "clang", "clang++",
        "arm-none-eabi-gcc", "arm-none-eabi-g++",
        "aarch64-linux-gnu-gcc",
        "x86_64-linux-gnu-gcc",
    ]

    def parse(self, raw_output: str) -> str:
        try:
            return self._parse_impl(raw_output)
        except Exception as e:
            return self.fallback(raw_output, reason=str(e))

    def _parse_impl(self, raw_output: str) -> str:
        # Try JSON diagnostics (clang --serialize-diagnostics or --json-diagnostics)
        stripped = raw_output.strip()
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return self._parse_json(stripped)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        return self._parse_text(raw_output)

    def _parse_json(self, raw_output: str) -> str:
        data = json.loads(raw_output)
        if isinstance(data, dict):
            data = data.get("diagnostics", [data])
        if not isinstance(data, list):
            data = [data]

        errors = []
        warnings = []
        for diag in data:
            severity = diag.get("severity", "").lower()
            msg = diag.get("message", "")
            loc = diag.get("location", {})
            file_path = loc.get("file", "?")
            line = loc.get("line", "?")
            entry = f"{file_path}:{line}: {msg}"
            if "error" in severity:
                errors.append(entry)
            elif "warning" in severity:
                warnings.append(entry)

        return self._format_output(errors, warnings)

    def _parse_text(self, raw_output: str) -> str:
        lines = raw_output.split("\n")
        errors = []
        warnings = []
        seen_errors = {}  # message -> count for dedup

        for line in lines:
            stripped = line.strip()

            # Skip noise lines
            if any(stripped.startswith(p) for p in _DROP_PREFIXES):
                continue
            if stripped.startswith("^") or stripped.startswith("|"):
                continue
            if stripped.startswith("note:") or ": note:" in stripped:
                continue

            m = _GCC_DIAG_RE.match(stripped)
            if m:
                file_path, lineno, col, severity, message = m.groups()
                entry = f"{file_path}:{lineno}:{col}: {message}"

                if severity in ("error", "fatal error"):
                    # Dedup identical error messages (e.g. undefined reference)
                    if message in seen_errors:
                        seen_errors[message] += 1
                    else:
                        seen_errors[message] = 1
                        errors.append(entry)
                elif severity == "warning":
                    warnings.append(entry)

        # Append dedup counts
        final_errors = []
        for entry in errors:
            # Extract just the message part after the last ": "
            msg = entry.rsplit(": ", 1)[-1] if ": " in entry else entry
            count = seen_errors.get(msg, 1)
            if count > 1:
                final_errors.append(f"{entry} (×{count})")
            else:
                final_errors.append(entry)

        return self._format_output(final_errors, warnings)

    def _format_output(self, errors: list[str], warnings: list[str]) -> str:
        result = []
        result.append(
            f"[BUILD] {len(errors)} error(s), {len(warnings)} warning(s)"
        )

        if errors:
            result.append("ERRORS:")
            for e in errors[:30]:
                result.append(f"  {e}")

        if warnings:
            if len(warnings) > 10:
                result.append(
                    f"WARNINGS: {len(warnings)} total (showing first 5)"
                )
                for w in warnings[:5]:
                    result.append(f"  {w}")
            else:
                result.append("WARNINGS:")
                for w in warnings:
                    result.append(f"  {w}")

        return "\n".join(result)
