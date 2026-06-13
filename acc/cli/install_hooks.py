import os
import sys
import shutil
import json
from pathlib import Path

COMMANDS = ["git", "pytest", "make", "gcc", "clang"]

MARKER_START = "# --- ACC CONTEXT COMPACTION HOOKS ---"
MARKER_END = "# --- END ACC HOOKS ---"

def _write_interceptor(bin_dir: Path):
    interceptor_path = bin_dir / "acc-interceptor"
    script = '''#!/bin/sh
# ACC transparent bash interceptor
COMMAND="$@"

# Run original command, capture output
RAW_OUTPUT=$(eval "$COMMAND" 2>&1)
EXIT_CODE=$?

# Pipe through ACC compression
COMPRESSED=$(echo "$RAW_OUTPUT" | acc-proxy compress "$COMMAND")

# If compression failed, return raw
if [ $? -ne 0 ]; then
    echo "$RAW_OUTPUT"
else
    echo "$COMPRESSED"
fi

exit $EXIT_CODE
'''
    interceptor_path.write_text(script, encoding="utf-8")
    os.chmod(interceptor_path, 0o755)

def _write_wrappers(bin_dir: Path):
    for cmd in COMMANDS:
        wrapper_path = bin_dir / cmd
        script = f'''#!/bin/sh
exec acc-proxy run {cmd} "$@"
'''
        wrapper_path.write_text(script, encoding="utf-8")
        os.chmod(wrapper_path, 0o755)

def _inject_path_to_rc(rc_path: Path):
    if not rc_path.exists():
        return
        
    content = rc_path.read_text(encoding="utf-8")
    if MARKER_START in content:
        return
        
    injection = f"\n{MARKER_START}\nexport PATH=\"$HOME/.acc-mcp/bin:$PATH\"\n{MARKER_END}\n"
    with rc_path.open("a", encoding="utf-8") as f:
        f.write(injection)

def _remove_path_from_rc(rc_path: Path):
    if not rc_path.exists():
        return
        
    content = rc_path.read_text(encoding="utf-8")
    if MARKER_START not in content:
        return
        
    lines = content.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if line == MARKER_START:
            skip = True
            continue
        if line == MARKER_END:
            skip = False
            continue
        if not skip:
            new_lines.append(line)
            
    rc_path.write_text('\n'.join(new_lines), encoding="utf-8")

def _install_claude_hooks():
    claude_hooks_dir = Path.home() / ".claude" / "hooks"
    if claude_hooks_dir.exists():
        hook_file = claude_hooks_dir / "pre_tool_use.json"
        
        hook_data = {}
        if hook_file.exists():
            try:
                hook_data = json.loads(hook_file.read_text(encoding="utf-8"))
            except Exception:
                hook_data = {}
                
        if "hooks" not in hook_data:
            hook_data["hooks"] = {}
            
        if "PreToolUse" not in hook_data["hooks"]:
            hook_data["hooks"]["PreToolUse"] = []
            
        # Check if already installed
        installed = False
        for h in hook_data["hooks"]["PreToolUse"]:
            if h.get("matcher") == "Bash":
                installed = True
                break
                
        if not installed:
            hook_data["hooks"]["PreToolUse"].append({
                "matcher": "Bash",
                "hooks": [{
                    "type": "command",
                    "command": "acc-interceptor"
                }]
            })
            hook_file.write_text(json.dumps(hook_data, indent=2), encoding="utf-8")
            print(f"Installed Claude Code hook to {hook_file}")

def _uninstall_claude_hooks():
    claude_hooks_dir = Path.home() / ".claude" / "hooks"
    hook_file = claude_hooks_dir / "pre_tool_use.json"
    if hook_file.exists():
        try:
            hook_data = json.loads(hook_file.read_text(encoding="utf-8"))
            if "hooks" in hook_data and "PreToolUse" in hook_data["hooks"]:
                original_len = len(hook_data["hooks"]["PreToolUse"])
                hook_data["hooks"]["PreToolUse"] = [
                    h for h in hook_data["hooks"]["PreToolUse"] 
                    if h.get("matcher") != "Bash" or not any(sub.get("command") == "acc-interceptor" for sub in h.get("hooks", []))
                ]
                if len(hook_data["hooks"]["PreToolUse"]) < original_len:
                    hook_file.write_text(json.dumps(hook_data, indent=2), encoding="utf-8")
                    print(f"Removed Claude Code hook from {hook_file}")
        except Exception as e:
            print(f"Failed to remove Claude Code hook cleanly: {e}")

def install():
    print("Installing ACC Transparent Bash Interceptor...")
    bin_dir = Path.home() / ".acc-mcp" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    _write_interceptor(bin_dir)
    _write_wrappers(bin_dir)
    print(f"Created executable wrappers in {bin_dir}")
    
    _inject_path_to_rc(Path.home() / ".bashrc")
    _inject_path_to_rc(Path.home() / ".zshrc")
    print("Injected PATH export into ~/.bashrc and ~/.zshrc")
    
    _install_claude_hooks()
    print("Installation complete. Please restart your terminal or run `source ~/.bashrc`.")

def uninstall():
    print("Uninstalling ACC Transparent Bash Interceptor...")
    bin_dir = Path.home() / ".acc-mcp" / "bin"
    
    try:
        if bin_dir.exists():
            shutil.rmtree(bin_dir)
            print(f"Removed directory {bin_dir}")
    except Exception as e:
        print(f"Failed to cleanly remove {bin_dir}: {e}")
        
    try:
        _remove_path_from_rc(Path.home() / ".bashrc")
        _remove_path_from_rc(Path.home() / ".zshrc")
        print("Removed PATH export from ~/.bashrc and ~/.zshrc")
    except Exception as e:
        print(f"Failed to cleanly remove PATH from rc files: {e}")
        
    _uninstall_claude_hooks()
    print("Uninstallation complete.")
