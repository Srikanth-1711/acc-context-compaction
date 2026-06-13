"""Parser for linter output: eslint, ruff, pylint, flake8, mypy."""

import json
import re
from collections import Counter
from acc.compaction.parsers.base import BaseParser

# Common linter output pattern: file:line:col: CODE message
_LINTER_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s*([A-Z]\d+)\s+(.+)$"
)
# Pylint-style: file:line:col: C1234: message (category)
_PYLINT_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s*([A-Z]\d+):\s+(.+)$"
)
# Mypy-style: file:line: error: message  [code]
_MYPY_RE = re.compile(
    r"^(.+?):(\d+):\s+(error|warning|note):\s+(.+?)(?:\s+\[(.+)\])?$"
)

_DROP_SEVERITY = {"note", "info", "convention", "refactor"}


class LinterParser(BaseParser):
    tool_names = ["eslint", "ruff", "pylint", "flake8", "mypy", "clang-tidy"]

    def parse(self, raw_output: str) -> str:
        try:
            return self._parse_impl(raw_output)
        except Exception as e:
            return self.fallback(raw_output, reason=str(e))

    def _parse_impl(self, raw_output: str) -> str:
        stripped = raw_output.strip()
        # Try JSON (eslint --format=json, ruff --output-format=json)
        if stripped.startswith("[") or stripped.startswith("{"):
            try:
                return self._parse_json(stripped)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

        return self._parse_text(raw_output)

    def _parse_json(self, raw_output: str) -> str:
        data = json.loads(raw_output)
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            return raw_output

        errors = []
        warnings = []
        rule_counts: Counter = Counter()

        for file_entry in data:
            file_path = file_entry.get("filePath", file_entry.get("file", "?"))
            messages = file_entry.get("messages", file_entry.get("diagnostics", []))
            if not isinstance(messages, list):
                continue
            for msg in messages:
                severity = msg.get("severity", 2)
                rule = msg.get("ruleId", msg.get("code", "?"))
                text = msg.get("message", "")
                line = msg.get("line", "?")

                entry = f"{file_path}:{line}: [{rule}] {text}"
                rule_counts[rule] += 1

                # ESLint: severity 2 = error, 1 = warning
                if severity == 2 or severity == "error":
                    errors.append(entry)
                elif severity == 1 or severity == "warning":
                    warnings.append(entry)

        return self._format_output(errors, warnings, rule_counts)

    def _parse_text(self, raw_output: str) -> str:
        lines = raw_output.split("\n")
        errors = []
        warnings = []
        rule_counts: Counter = Counter()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Skip progress/summary lines
            if stripped.startswith("---") or stripped.startswith("==="):
                continue
            if "Your code has been rated" in stripped:
                continue
            if stripped.startswith("Found ") and "error" in stripped:
                continue

            # Try each regex pattern
            entry = None
            rule = None
            severity = None

            m = _LINTER_RE.match(stripped)
            if m:
                file_path, lineno, col, rule, msg = m.groups()
                entry = f"{file_path}:{lineno}:{col}: [{rule}] {msg}"
                severity = self._classify_rule(rule)

            if not m:
                m = _PYLINT_RE.match(stripped)
                if m:
                    file_path, lineno, col, rule, msg = m.groups()
                    entry = f"{file_path}:{lineno}:{col}: [{rule}] {msg}"
                    severity = self._classify_rule(rule)

            if not m:
                m = _MYPY_RE.match(stripped)
                if m:
                    file_path, lineno, sev_str, msg = m.group(1, 2, 3, 4)
                    rule = m.group(5) or "mypy"
                    entry = f"{file_path}:{lineno}: [{rule}] {msg}"
                    severity = sev_str

            if entry and severity:
                if severity in _DROP_SEVERITY:
                    continue
                rule_counts[rule] += 1
                if severity == "error":
                    errors.append(entry)
                else:
                    warnings.append(entry)

        return self._format_output(errors, warnings, rule_counts)

    def _classify_rule(self, rule: str) -> str:
        """Classify a rule code into error/warning/note severity."""
        if not rule:
            return "warning"
        first = rule[0].upper()
        # Pylint: E=error, W=warning, C=convention, R=refactor
        # Ruff/flake8: E=error, W=warning, F=pyflakes
        if first == "E" or first == "F":
            return "error"
        elif first in ("C", "R"):
            return "convention"
        return "warning"

    def _format_output(
        self,
        errors: list[str],
        warnings: list[str],
        rule_counts: Counter,
    ) -> str:
        result = []
        result.append(f"[LINT] {len(errors)} error(s), {len(warnings)} warning(s)")

        # Collapse rules firing > 5 times
        collapsed_rules = {r: c for r, c in rule_counts.items() if c > 5}

        if errors:
            result.append("ERRORS:")
            shown_errors = set()
            for e in errors[:30]:
                # Check if this error's rule is collapsed
                rule_match = re.search(r"\[(.+?)\]", e)
                if rule_match:
                    rule = rule_match.group(1)
                    if rule in collapsed_rules and rule in shown_errors:
                        continue
                    if rule in collapsed_rules:
                        shown_errors.add(rule)
                        result.append(f"  {e}")
                        result.append(
                            f"    ↳ [{rule}] {collapsed_rules[rule]} total occurrences"
                        )
                        continue
                result.append(f"  {e}")

        if warnings:
            if len(warnings) > 10:
                result.append(f"WARNINGS: {len(warnings)} total (showing first 5)")
                for w in warnings[:5]:
                    result.append(f"  {w}")
            else:
                result.append("WARNINGS:")
                for w in warnings:
                    result.append(f"  {w}")

        return "\n".join(result)
