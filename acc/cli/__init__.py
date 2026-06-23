import typer
from pathlib import Path
import json
import sys
from typing import Optional

app = typer.Typer(help="ACC — Agentic Context Compaction CLI")

@app.command()
def doctor():
    """Check ACC installation health."""
    checks = {
        "python": sys.version_info >= (3, 10),
        "tiktoken": _check_module("tiktoken"),
        "sqlmodel": _check_module("sqlmodel"),
        "mcp": _check_module("mcp"),
        "tomli": _check_module("tomli"),
    }
    
    all_ok = True
    for name, ok in checks.items():
        status = "✅" if ok else "❌"
        if not ok:
            all_ok = False
        typer.echo(f"{status} {name}")
    
    # Check database
    db_path = Path.home() / ".acc" / "acc_telemetry.db"
    typer.echo(f"{'✅' if db_path.exists() else '⚠️'}  telemetry database ({db_path})")
    
    # Check trusted hashes
    trusted_file = Path.home() / ".acc" / "trusted.json"
    typer.echo(f"{'✅' if trusted_file.exists() else '⚠️'}  trusted hashes ({trusted_file})")
    
    if not all_ok:
        typer.echo("\n❌ Some checks failed. Run: pip install acc-mcp[all]")
        raise typer.Exit(1)
    else:
        typer.echo("\n✅ ACC is healthy!")

@app.command()
def trust(path: Path):
    """Trust a TOML filter configuration file."""
    from acc.filters.toml_loader import trust_file
    if not path.exists():
        typer.echo(f"❌ File not found: {path}")
        raise typer.Exit(1)
    trust_file(path)
    typer.echo(f"✅ Trusted: {path}")

@app.command()
def analytics(period: str = "all"):
    """Show token savings analytics."""
    from acc.telemetry.tracker import AnalyticsTracker
    tracker = AnalyticsTracker()
    data = tracker.get_json(period)
    
    if "error" in data:
        typer.echo(f"❌ Error: {data['error']}")
        raise typer.Exit(1)
    
    typer.echo(f"\n📊 ACC Analytics ({period})\n")
    typer.echo(f"  Runs:        {data['runs']}")
    typer.echo(f"  Raw tokens:  {data['raw_tokens']:,}")
    typer.echo(f"  Output:      {data['output_tokens']:,}")
    typer.echo(f"  Saved:       {data['saved_tokens']:,}")
    typer.echo(f"  Reduction:   {data['reduction_pct']}%")

@app.command()
def install(agent: str = typer.Option("claude", help="Agent to configure: claude, cursor, windsurf")):
    """Auto-configure ACC for an AI coding agent."""
    mcp_config = {
        "mcpServers": {
            "acc": {
                "command": "python",
                "args": ["-m", "acc.mcp_server"],
                "env": {}
            }
        }
    }
    
    if agent == "claude":
        config_dir = Path.home() / "Library" / "Application Support" / "Claude"
        if sys.platform == "win32":
            config_dir = Path.home() / "AppData" / "Roaming" / "Claude"
        config_file = config_dir / "claude_desktop_config.json"
    elif agent == "cursor":
        config_dir = Path.home() / ".cursor"
        config_file = config_dir / "mcp.json"
    elif agent == "windsurf":
        typer.echo("⚠️ Windsurf MCP config location varies. Please manually add:")
        typer.echo(json.dumps(mcp_config, indent=2))
        return
    else:
        typer.echo(f"❌ Unknown agent: {agent}")
        raise typer.Exit(1)
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    existing = {}
    if config_file.exists():
        try:
            existing = json.loads(config_file.read_text())
        except json.JSONDecodeError:
            pass
    
    if "mcpServers" not in existing:
        existing["mcpServers"] = {}
    
    existing["mcpServers"]["acc"] = mcp_config["mcpServers"]["acc"]
    config_file.write_text(json.dumps(existing, indent=2))
    typer.echo(f"✅ Installed ACC MCP server for {agent}")
    typer.echo(f"   Config: {config_file}")

def _check_module(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    app()
