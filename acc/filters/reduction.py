import os
import tempfile
import datetime
from collections import deque
from typing import Iterable, List

NOISE_PREFIXES = [
    "INFO  ", "DEBUG ", "Downloading", "Resolving", "Fetching",
]

def filter_noise(lines: Iterable[str]) -> List[str]:
    out = []
    for line in lines:
        stripped = line.rstrip("\n")
        if not stripped:
            continue
        if any(stripped.startswith(p) for p in NOISE_PREFIXES):
            continue
        out.append(stripped)
    return out

def dedup(lines: Iterable[str], window: int = 5) -> List[str]:
    out = []
    recent = deque(maxlen=window)
    count = 0
    last = None
    for line in lines:
        if line == last:
            count += 1
            continue
        if count > 0 and last is not None:
            out.append(f"{last} (repeated {count} times)")
        if line in recent:
            out.append(line)
        else:
            out.append(line)
            recent.append(line)
        last = line
        count = 0
    if count > 0 and last is not None:
        out.append(f"{last} (repeated {count} times)")
    return out

def truncate(lines: List[str], max_lines: int, raw_lines: List[str] = None) -> List[str]:
    if len(lines) <= max_lines:
        return lines
    
    head = lines[: max_lines // 2]
    tail = lines[-max_lines // 2 :]
    
    tee_msg = "--- snip: middle omitted by ACC ---"
    if raw_lines:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(tempfile.gettempdir(), f"acc_tee_{timestamp}.log")
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.writelines(raw_lines)
            tee_msg = f"--- snip: middle omitted by ACC. Full raw log saved to {log_file} ---"
        except Exception:
            pass
            
    return head + [tee_msg] + tail
