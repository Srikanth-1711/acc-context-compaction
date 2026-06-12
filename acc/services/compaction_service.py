import subprocess
import sys
import shutil
from pathlib import Path
from typing import List

from acc.core.logger import log
from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager

def run_compaction(cmd: List[str], cwd: Path | None = None) -> str:
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

    pm = ProfileManager()
    base_cmd = cmd[0].lower()
    if base_cmd.endswith(".exe"):
        base_cmd = base_cmd[:-4]
        
    profile = pm.load_profile(base_cmd)
    
    # Git has subcommands, let's just use the generic git profile for now
    if "git" in base_cmd:
        profile = pm.load_profile("git")

    pipeline = FilterPipeline(profile)
    text = pipeline.execute(raw)

    return text
