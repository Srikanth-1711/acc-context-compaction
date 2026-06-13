"""Parser for pytest output. Handles both plain text and JSON report format."""

import json
from acc.compaction.parsers.base import BaseParser


class PytestParser(BaseParser):
    tool_names = ["pytest", "py.test"]

    def parse(self, raw_output: str) -> str:
        try:
            return self._parse_impl(raw_output)
        except Exception as e:
            return self.fallback(raw_output, reason=str(e))

    def _parse_impl(self, raw_output: str) -> str:
        # Try JSON format first (user may have used --json-report)
        stripped = raw_output.strip()
        if stripped.startswith("{"):
            try:
                return self._parse_json(stripped)
            except (json.JSONDecodeError, KeyError):
                pass

        return self._parse_text(raw_output)

    def _parse_json(self, raw_output: str) -> str:
        data = json.loads(raw_output)
        tests = data.get("tests", [])
        failed = [t for t in tests if t.get("outcome") == "failed"]
        passed_count = sum(1 for t in tests if t.get("outcome") == "passed")

        lines = []
        summary = data.get("summary", {})
        total = summary.get("total", len(tests))
        fail_count = summary.get("failed", len(failed))
        lines.append(f"[PYTEST] {fail_count} failed, {passed_count} passed ({total} total)")

        if failed:
            lines.append("FAILURES:")
            for t in failed[:20]:
                nodeid = t.get("nodeid", "unknown")
                msg = ""
                call = t.get("call", {})
                if isinstance(call, dict):
                    crash = call.get("crash", {})
                    msg = crash.get("message", "") if isinstance(crash, dict) else ""
                lines.append(f"  FAILED {nodeid} — {msg}")

        if passed_count > 0:
            lines.append(f"({passed_count} passed tests suppressed)")

        return "\n".join(lines)

    def _parse_text(self, raw_output: str) -> str:
        lines = raw_output.split("\n")
        failures = []
        summary_line = None
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Capture FAILED lines — handles both formats:
            # "FAILED tests/test_x.py::test_y - reason"
            # "FAILED tests/test_x.py::test_y [reason]"
            if stripped.startswith("FAILED "):
                failure_block = [stripped]
                # Grab next few lines for traceback context (up to 5)
                for j in range(1, 6):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line and not next_line.startswith("FAILED "):
                            failure_block.append(next_line)
                        else:
                            break
                failures.append("\n  ".join(failure_block))
                i += len(failure_block)
                continue

            # Capture summary line
            if ("failed" in stripped and "passed" in stripped) or (
                "failed" in stripped and "error" in stripped
            ):
                if "=" in stripped or "short test summary" not in stripped.lower():
                    summary_line = stripped

            i += 1

        # Count passed lines for suppression notice
        passed_count = sum(
            1
            for l in lines
            if " PASSED" in l or l.strip().endswith("PASSED")
        )

        result = []
        if summary_line:
            result.append(f"[PYTEST] {summary_line}")
        elif failures:
            result.append(f"[PYTEST] {len(failures)} failures detected")
        else:
            result.append("[PYTEST] No failures detected")

        if failures:
            result.append("FAILURES:")
            for f in failures[:20]:
                result.append(f"  {f}")

        if passed_count > 0:
            result.append(f"({passed_count} passed tests suppressed)")

        return "\n".join(result)
