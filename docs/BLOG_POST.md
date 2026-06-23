# The Context Engineering Stack: Why I Built ACC by Stealing from 4 Better Projects

I spent 3 months analyzing RTK, Caveman Code, Ponytail, and Supermemory.  
Each solves one piece of the LLM context problem. None solves all of it.

So I stole their best ideas and built ACC — the unified context optimizer.

## What I Stole

### From RTK: The TOML Filter Engine
RTK has 100+ command-specific filters in Rust. I ported the 8-stage pipeline to Python:
strip_ansi → regex_replace → regex_drop → regex_keep → line_dedup → smart_truncate → head_tail → on_empty

The innovation: **user-extensible TOML filters with a trust model**.  
Hash the config, store it in `~/.acc/trusted.json`, verify before loading.  
Prevents supply-chain attacks via malicious regex filters.

### From Caveman: Deterministic Compression
Caveman's LLMLingua-2 is impressive but requires ONNX. I implemented a lightweight fallback:
- Keep structurally important lines (signatures, imports, errors)
- Drop boilerplate (compilation messages, progress bars)
- Score lines by information density

No ML dependencies. Works everywhere.

### From Supermemory: Temporal Memory
Supermemory's knowledge graph is elegant. I built a lightweight triple-store:
- (subject, predicate, object) with valid_from/valid_until
- Automatic contradiction detection: new fact → old fact deprecated
- Keyword search with TF-IDF scoring (embeddings coming in v0.3)

### From Ponytail: YAGNI Philosophy
Ponytail's "lazy ladder" prevents unnecessary code generation.  
ACC applies the same philosophy to **context**: the best token is the one you never send.

## What I Added

### O(1) Cross-Turn Dedup
RTK has no session memory. Caveman has no dedup.  
ACC fingerprints output with `(len, md5(first_256), md5(last_256))` and persists across turns.

Repeated `git status` in the same session? → "[Output identical to turn #3]"

### MCP-Native Architecture
RTK is CLI-only. Supermemory is backend-dependent.  
ACC is an MCP server — one `pip install`, auto-configures Claude/Cursor/Windsurf.

### Real-Time Analytics
`acc://analytics` resource lets agents query their own savings.  
"How much money did I save this week?" → structured JSON response.

## The Numbers

| Tool | Setup | Token Reduction | Cross-Session Dedup | Memory | Compression |
|------|-------|----------------|---------------------|--------|-------------|
| Raw | — | 0% | ❌ | ❌ | ❌ |
| RTK | `cargo install` | 50-90% | ❌ | ❌ | ❌ |
| Caveman | Complex | 30-70% | ❌ | ❌ | ✅ ML |
| Ponytail | Copy-paste | 0% (output only) | ❌ | ❌ | ❌ |
| Supermemory | SaaS signup | 0% | ❌ | ✅ Graph | ❌ |
| **ACC** | **`pip install`** | **40-90%** | **✅ O(1)** | **✅ Triple-store** | **✅ Deterministic** |

## The Meta-Insight

The emerging "Context Engineering" stack has four layers:
1. **Filtering** (RTK/ACC) — Reduce what goes in
2. **Compression** (Caveman/ACC) — Compress what stays
3. **Behavior** (Ponytail) — Reduce what comes out
4. **Memory** (Supermemory/ACC) — Remember what matters

No single project does all four. ACC is the first unified attempt.

## What's Next

- v0.3: Semantic search with sentence-transformers
- v0.4: LLMLingua-2 ONNX integration (optional)
- v0.5: Subagent orchestration with worktree isolation

## Try It

```bash
pip install acc-mcp
acc install --claude
acc doctor
```

[GitHub](https://github.com/Srikanth-1711/acc-context-compaction) · [PyPI](https://pypi.org/project/acc-mcp/)
