# ACC — Inline Reversible Compression for AI Agents

> The only context optimizer where compressed output carries its own recovery data.
> No ML models. Zero config.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage](https://img.shields.io/badge/coverage-89%25+-brightgreen.svg)]()

## The Problem

AI agents burn 50-90% of their context window on noise:
- `cargo build` → 500 lines of "Compiling..."
- `pytest` → every passing test listed
- `git status` → verbose headers on a clean repo

Existing solutions either:
- **Require ML models** (500ms cold start, 100MB RAM)
- **Need configuration** (which algorithm? what ratio?)
- **Lose dropped context forever** (no way to recover)

## The Solution: Inline Reversible Compression (IRC)

ACC replaces noise with **self-contained recovery tokens**:

```text
Before:  500 lines of cargo build output
After:   [cargo build: 12 errors, 3 warnings]
         [...487 lines compressed: irc:eJxzz...]
```

The `irc:` token contains zlib-compressed original lines + metadata.
When the agent needs full context, `acc_expand` recovers it instantly.

**No model loading. The compressed text IS the storage.**

## Why IRC Changes Everything

| | Headroom | RTK | ACC |
|--|----------|-----|-----|
| Cold start | ~500ms | ~10ms | **~50ms** |
| Memory | ~100MB | ~5MB | **~5MB** |
| Config required | Yes | No | **No** |
| Cross-machine | ❌ (SQLite) | ✅ | **✅ (token is portable)** |
| Recovery | External DB | None | **Inline (self-contained)** |
| Accuracy (code) | 99.2% | ~85% | **~98%** |

## Quick Start

```bash
pip install acc-mcp
acc install --claude
acc doctor
```

## How It Works

```
[Agent calls tool] → acc_run()
  → Execute command safely (30s timeout, 10MiB cap)
  → Dedup check (SHA-256, cross-turn, 7-day TTL)
  → Filter (10 built-in command filters)
  → Score lines (keep errors/signatures, drop noise)
  → IRC compress (replace drops with recovery token)
  → Return structured response with token
```

If the agent later needs full context:

```
[Agent calls] → acc_expand("...irc:eJxzz...")
  → Decode base64 → zlib decompress → restore original
```

## MCP Tools & Resources

| Type | Name | Description |
|------|------|-------------|
| Tool | `acc_run` | Execute command with full optimization pipeline |
| Tool | `acc_expand` | Recover original text from IRC token |
| Tool | `acc_remember` | Save facts into temporal memory |
| Tool | `acc_search` | Search temporal memory (keyword or temporal) |
| Resource | `acc://analytics` | Markdown summary of token savings |
| Resource | `acc://analytics/{period}` | JSON analytics for day/week/month/all |
| Resource | `acc://status` | Health check |

## Built-in Filters

| Command | Reduction | Recovery |
|---|---|---|
| git status (clean) | 97% | acc_expand |
| cargo build | 90% | acc_expand |
| pytest (all pass) | 85% | acc_expand |
| npm test | 80% | acc_expand |

## User-Extensible Filters

Create `.acc/filters.toml`:

```toml
[filter.my-command]
command = "my-tool"
stages = [
    {name = "strip_ansi"},
    {name = "regex_drop", pattern = "^INFO"},
    {name = "smart_truncate", max_lines = 20}
]
```

Trust it: `acc trust .acc/filters.toml`

## Analytics

```bash
acc analytics --week
# Or query via MCP: acc://analytics/week
```

## Architecture

- **Language:** Python 3.10+
- **MCP:** FastMCP server with 4 tools + 3 resources
- **Compression:** Deterministic line-scoring + IRC tokens
- **Dedup:** SHA-256 hashing with 7-day TTL and LRU eviction
- **Telemetry:** Optional SQLite (analytics only, never in critical path)
- **Security:** No shell=True, no eval, hash-verified TOML filters

## License

MIT
