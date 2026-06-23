# Show HN: ACC — A unified context optimizer for AI coding agents

I built ACC after analyzing 5 "context engineering" projects (RTK, Caveman, Ponytail, Supermemory, and my own). Each solves one piece of the problem. ACC unifies them into a single MCP server.

## What it does

- **Filters** CLI output (10 built-in command filters, user-extensible TOML)
- **Dedups** identical output across turns (O(1) triple-hash fingerprinting)
- **Compresses** via deterministic line-scoring (no ML dependencies)
- **Remembers** facts in a temporal triple-store (auto-contradiction detection)

## Why MCP-native matters

RTK is a CLI proxy (hard to integrate). Caveman is a full agent (heavy). Ponytail is just prompts (thin). Supermemory is backend-dependent (complex).

ACC is `pip install acc-mcp`, then `acc install --claude`. One command.

## The numbers

| Command | Raw | ACC | Savings |
|---------|-----|-----|---------|
| `git status` (clean) | 200 tokens | 5 | 97.5% |
| `cargo build` | 15,000 | 1,500 | 90% |
| `pytest` (100 pass) | 5,000 | 750 | 85% |
| Cross-session `ls` | 500 | 30 | 94% |

## Try it

```bash
pip install acc-mcp
acc install --claude
acc doctor
```

GitHub: https://github.com/Srikanth-1711/acc-context-compaction

Questions?
The code is MIT licensed. 86% test coverage. Built in Python 3.10+.
What would you want to see in v0.3?
