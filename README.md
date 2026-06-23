# ACC — Agentic Context Compaction

> The unified context optimizer for AI coding agents.  
> Filter · Dedup · Compress · Remember — inside a single MCP server.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)]()

## The Problem

AI coding agents burn tokens on noisy tool output:

- `cargo build` dumps 500 lines of "Compiling..."
- `git status` returns verbose headers
- `pytest` lists every passing test
- Repeated `ls` commands in the same session return identical output

Every wasted token costs money, fills context windows, and degrades reasoning.

## The Solution

ACC is a **unified MCP server** that optimizes context in four layers:

| Layer | What It Does | Inspired By |
|-------|-------------|-------------|
| **Filter** | 10 built-in command filters + user-extensible TOML | RTK |
| **Dedup** | O(1) cross-turn output deduplication | ACC original |
| **Compress** | Deterministic line-scoring fallback | Caveman |
| **Remember** | Temporal knowledge graph with contradiction detection | Supermemory |

## Quick Start

```bash
pip install acc-mcp
acc install --claude    # Auto-configures Claude Code MCP
acc doctor              # Verify installation
```

## Usage

Once installed, your agent's tool calls are automatically optimized:

```python
# Agent calls this (transparently)
acc_run("cargo test")

# Returns:
{
    "output": "[cargo test: all passed]",
    "tokens_saved": 2847,
    "compression_ratio": 0.02,
    "deduped": false,
    "memories_injected": 2
}
```

### Built-in Filters

| Command | Typical Reduction |
|---------|-------------------|
| `git status` | 97% (→ "[git status: clean]") |
| `cargo build` | 90% (errors only) |
| `pytest` | 85% (failures only) |
| `npm test` | 80% |
| `ls -la` | 50% |

### User-Extensible Filters

Create `.acc/filters.toml` in your project:

```toml
[filter.my-command]
command = "my-tool"
stages = [
    {name = "strip_ansi"},
    {name = "regex_drop", pattern = "^INFO"},
    {name = "smart_truncate", max_lines = 20}
]
```

Then trust it: `acc trust .acc/filters.toml`

### Analytics

Query your savings in real-time:

```bash
acc analytics --week    # CLI
# Or via MCP resource: acc://analytics/week
```

## Architecture

```plain
User/Agent Command
  → acc_run() [MCP tool]
    → Memory retrieval (temporal facts)
    → Safe execution (subprocess, 30s timeout, 10MiB cap)
    → O(1) dedup check (triple-hash fingerprinting)
    → 8-stage filter pipeline (built-in or TOML)
    → Deterministic compression
    → Telemetry logging (SQLite)
    → Structured response with metadata
```

## Why ACC vs. Alternatives

| | RTK | Caveman | Ponytail | Supermemory | ACC |
|---|---|---|---|---|---|
| **Type** | CLI proxy | Full agent | Prompt skill | Backend service | MCP server |
| **Filtering** | ✅ 100+ commands | ❌ | ❌ | ❌ | ✅ 10 built-in + TOML |
| **Dedup** | ❌ | ❌ | ❌ | ❌ | ✅ O(1) cross-turn |
| **Compression** | ❌ | ✅ LLMLingua | ❌ | ❌ | ✅ Deterministic |
| **Memory** | ❌ | ❌ | ❌ | ✅ Graph | ✅ Temporal triple-store |
| **Setup** | cargo install | Complex | Copy-paste | SaaS signup | pip install |

## Benchmarks

See `benchmark/run.py`. Typical results:

| Suite | Raw Tokens | ACC Output | Savings |
|-------|------------|------------|---------|
| `git status` (clean) | 200 | 5 | 97.5% |
| `cargo build` (200 deps) | 15,000 | 1,500 | 90% |
| `pytest` (100 tests) | 5,000 | 750 | 85% |
| Cross-session `ls` dedup | 500 | 30 | 94% |

## Development

```bash
git clone https://github.com/YOURNAME/acc-context-compaction
cd acc-context-compaction
pip install -e ".[dev]"
pytest --cov=acc --cov-fail-under=80
```

## License

MIT
