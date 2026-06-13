import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

from acc.core.logger import log
from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager
from acc.compaction.parsers import get_parser
from acc.compaction.dedup_cache import get_session_cache

def run_compaction(cmd: List[str], cwd: Path | None = None) -> str:
    cache = get_session_cache()
    cache.next_turn()
    log.info("Running compaction service", extra={"cmd": cmd, "cwd": str(cwd)})
    if len(cmd) == 1 and " " in cmd[0]:
        cmd = cmd[0].split(" ")
        
    if sys.platform == "win32":
        resolved = shutil.which(cmd[0])
        if resolved:
            cmd[0] = resolved
            
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = proc.stdout.read()
    proc.wait()

    # Check dedup cache before expensive parsing
    suppressed = cache.check(raw)
    if suppressed:
        return suppressed

    pm = ProfileManager()
    base_cmd = cmd[0].lower()
    if base_cmd.endswith(".exe"):
        base_cmd = base_cmd[:-4]
    # Strip path to get just the executable name
    base_cmd = base_cmd.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]

    # Try structured parsing first via plugin parsers
    parser = get_parser(base_cmd)
    if parser:
        try:
            raw = parser.parse(raw)
        except Exception:
            log.warning("Parser failed, falling back to raw",
                        extra={"cmd": base_cmd})

    profile = pm.load_profile(base_cmd)
    
    # Git has subcommands, let's just use the generic git profile for now
    if "git" in base_cmd:
        profile = pm.load_profile("git")

    pipeline = FilterPipeline(profile)
    text = pipeline.execute(raw)

    return text
