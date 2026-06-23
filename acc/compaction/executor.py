import subprocess
import shlex
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    stdout: str
    exit_code: int
    error: Optional[str] = None
    truncated: bool = False

def execute_command(
    command: List[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    max_output_bytes: int = 10 * 1024 * 1024  # 10 MiB
) -> ExecutionResult:
    """
    Safely executes a shell command with timeout and output limits.
    """
    if not command:
        return ExecutionResult("", 1, error="[Command is empty]")

    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            # Windows specific flags to prevent shell=True
        )
        
        chunks = []
        total_chars = 0
        truncated = False
        
        try:
            # We use communicate with a timeout to read stdout
            stdout_data, _ = proc.communicate(timeout=timeout)
            
            # Note: communicate reads the entire output. To strictly enforce max_output_bytes
            # *during* reading without loading everything into memory, we would need to read
            # iteratively. However, for 10MiB, loading to memory is usually fine before truncation.
            # Let's enforce truncation on the result:
            if len(stdout_data.encode('utf-8')) > max_output_bytes:
                truncated = True
                # Truncate at char level roughly
                # A safer way to enforce during read is a custom loop.
                # Since we already have output here, we'll just truncate it.
                stdout_data = stdout_data[:max_output_bytes]
                stdout_data += "\n... [ACC FATAL: Output exceeded 10MiB hard limit. Truncated.]\n"
            
            return ExecutionResult(stdout=stdout_data, exit_code=proc.returncode, truncated=truncated)

        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return ExecutionResult("", -1, error=f"[Command timed out after {timeout}s]")
            
    except FileNotFoundError:
        return ExecutionResult("", 127, error=f"[Command not found: {command[0]}]")
    except PermissionError:
        return ExecutionResult("", 126, error=f"[Permission denied: {command[0]}]")
    except OSError as e:
        return ExecutionResult("", 1, error=f"[OS error: {e}]")
