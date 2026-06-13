import sys
import os
import subprocess
import threading
import time
from acc.compaction.parsers import get_parser
from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager
from acc.compaction.dedup_cache import get_session_cache

def _read_stdin_timeout(timeout=5.0):
    lines = []
    def _read():
        try:
            lines.append(sys.stdin.read())
        except Exception:
            pass
            
    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None
    return lines[0] if lines else ""

def compress_logic(raw_text: str, base_cmd: str) -> str:
    cache = get_session_cache()
    # Apply dedup cache
    suppressed = cache.check(raw_text)
    if suppressed:
        return suppressed
        
    parser = get_parser(base_cmd)
    parsed_text = raw_text
    if parser:
        try:
            parsed_text = parser.parse(raw_text)
        except Exception:
            pass
            
    pm = ProfileManager()
    profile_name = "git" if "git" in base_cmd else base_cmd
    pipeline = FilterPipeline(pm.load_profile(profile_name))
    return pipeline.execute(parsed_text)

def main():
    if len(sys.argv) < 2:
        print("Usage: acc-proxy <run|compress> [args...]")
        sys.exit(1)
        
    action = sys.argv[1]
    
    if action == "compress":
        if len(sys.argv) < 3:
            # We need the command name to know which profile to load
            print("Usage: acc-proxy compress <command>")
            sys.exit(1)
            
        full_cmd = sys.argv[2:]
        base_cmd = full_cmd[0].lower().replace('.exe', '').rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
        
        raw_input = _read_stdin_timeout(5.0)
        if raw_input is None:
            # Timeout
            sys.exit(1)
            
        try:
            compressed = compress_logic(raw_input, base_cmd)
            sys.stdout.write(compressed)
            sys.exit(0)
        except Exception:
            sys.exit(1)
            
    elif action == "run":
        if len(sys.argv) < 3:
            print("Usage: acc-proxy run <command> [args...]")
            sys.exit(1)
            
        cmd = sys.argv[2:]
        base_cmd = cmd[0].lower().replace('.exe', '').rsplit('/', 1)[-1].rsplit('\\', 1)[-1]
        
        # Strip ~/.acc-mcp/bin from PATH to prevent infinite wrapper recursion
        env = os.environ.copy()
        paths = env.get("PATH", "").split(os.pathsep)
        acc_bin = os.path.expanduser("~/.acc-mcp/bin")
        paths = [p for p in paths if p != acc_bin]
        env["PATH"] = os.pathsep.join(paths)
        
        cache = get_session_cache()
        cache.next_turn()
        
        try:
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            raw, _ = proc.communicate()
            exit_code = proc.returncode
        except Exception as e:
            print(f"acc-proxy: failed to run {' '.join(cmd)}: {e}")
            sys.exit(1)
            
        if exit_code != 0 and not raw.strip():
            sys.exit(exit_code)
            
        try:
            compressed = compress_logic(raw, base_cmd)
            sys.stdout.write(compressed)
        except Exception:
            sys.stdout.write(raw)
            
        sys.exit(exit_code)
        
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()
