import typer
from typing import List
from pathlib import Path
from acc.services.compaction_service import run_compaction

app = typer.Typer(help="ACC CLI Proxy: compact command output for AI agents")

@app.command()
def run(
    cmd: List[str] = typer.Argument(..., help="Command to run, e.g. 'pytest -q'"),
    cwd: str = typer.Option(".", help="Working directory"),
    hint: str = typer.Option("", help="Optional hint about what you care about"),
):
    """
    Run an arbitrary command and print compacted output.
    """
    out = run_compaction(cmd, Path(cwd))
    print(out)

if __name__ == "__main__":
    app()
