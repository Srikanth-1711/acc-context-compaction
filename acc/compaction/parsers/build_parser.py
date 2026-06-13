"""Parser for build system output: make, cmake, ninja, cargo, gradle, mvn."""

import re
from acc.compaction.parsers.base import BaseParser

# Lines to drop from build output
_DROP_PATTERNS = (
    "Entering directory",
    "Leaving directory",
    "make[",
    "Nothing to be done",
    "is up to date",
    "Compiling ",
    "Linking ",
    "Building ",
    "Scanning dependencies",
    "Built target ",
    "Installing ",
    "-- ",  # cmake status messages
    "[  ",  # progress percentages like [  5%]
    "[ ",
    "UP-TO-DATE",
    "NO-SOURCE",
    "Downloading ",
    "Download ",
    "> Task :",  # gradle task lines
)

_ERROR_PATTERNS = (
    "error:",
    "Error:",
    "ERROR:",
    "FAILED",
    "FAILURE",
    "BUILD FAILED",
    "BUILD FAILURE",
    "fatal:",
    "undefined reference",
    "cannot find",
    "not found",
    "No rule to make target",
    "*** ",  # make error marker
)


class BuildParser(BaseParser):
    tool_names = ["make", "cmake", "ninja", "cargo", "gradle", "mvn", "maven"]

    def parse(self, raw_output: str) -> str:
        try:
            return self._parse_impl(raw_output)
        except Exception as e:
            return self.fallback(raw_output, reason=str(e))

    def _parse_impl(self, raw_output: str) -> str:
        lines = raw_output.split("\n")

        # Detect if build succeeded or failed
        has_failure = any(
            any(ep in line for ep in _ERROR_PATTERNS)
            for line in lines[-50:]  # check last 50 lines
        )

        if not has_failure:
            # Successful build — super terse
            total_lines = len([l for l in lines if l.strip()])
            return f"[BUILD OK] Completed successfully ({total_lines} output lines suppressed)"

        # Build failed — extract error context
        return self._extract_failure(lines)

    def _extract_failure(self, lines: list[str]) -> str:
        error_lines = []
        context_lines = []
        total_lines = len(lines)
        dropped = 0

        # First pass: find all error lines and their indices
        error_indices = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            if any(stripped.startswith(p) or stripped.startswith(p.lstrip()) for p in _DROP_PATTERNS):
                dropped += 1
                continue

            if any(ep in stripped for ep in _ERROR_PATTERNS):
                error_indices.append(i)
                error_lines.append(stripped)

        # Second pass: grab context around first error (±5 lines)
        if error_indices:
            first_error = error_indices[0]
            start = max(0, first_error - 3)
            end = min(len(lines), first_error + 8)
            for i in range(start, end):
                stripped = lines[i].strip()
                if stripped and not any(stripped.startswith(p) for p in _DROP_PATTERNS):
                    context_lines.append(stripped)

        result = []
        result.append(
            f"[BUILD FAILED] {len(error_lines)} error(s) in {total_lines} output lines "
            f"({dropped} noise lines suppressed)"
        )

        if context_lines:
            result.append("ERROR CONTEXT:")
            for c in context_lines[:20]:
                result.append(f"  {c}")

        # If there are more errors beyond the first, list them
        if len(error_lines) > 1:
            result.append(f"ALL ERRORS ({len(error_lines)}):")
            for e in error_lines[:15]:
                result.append(f"  {e}")
            if len(error_lines) > 15:
                result.append(f"  ... and {len(error_lines) - 15} more")

        return "\n".join(result)
