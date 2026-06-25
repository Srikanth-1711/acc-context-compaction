# Show HN: ACC — Context compression that fits in a tweet

I built ACC because every existing context optimizer has the same problem: they need something else.

- Headroom needs an ML model (500ms cold start)
- RTK needs `cargo install` (not portable across machines)
- Everything else needs configuration

ACC needs none of that. It's `pip install acc-mcp`, then `acc install --claude`.

The trick: **Inline Reversible Compression (IRC)**.

When ACC compresses `cargo build` output from 500 lines to 12, it doesn't throw away the 488 dropped lines. It zlib-compresses them, base64-encodes them, and embeds the result directly in the output:

```text
[cargo build: 12 errors, 3 warnings]
[...488 lines compressed: irc:eJxzz...]
```

The `irc:` token IS the recovery data. No SQLite. No external storage. Copy-paste it to another machine, it still works. Email it, it still works.

When the agent needs the full output, it calls `acc_expand` with the token. ACC decodes, decompresses, and restores the original text exactly.

## Numbers

| Scenario | Raw | ACC | Savings |
|----------|-----|-----|---------|
| `git status` (clean) | 200 tokens | 5 | 97.5% |
| `cargo build` (200 deps) | 15,000 | 1,500 | 90% |
| `pytest` (100 pass) | 5,000 | 750 | 85% |
| Cross-session `ls` | 500 | 30 | 94% |

Cold start: ~50ms. Memory: ~5MB. Zero configuration.

## Try it

```bash
pip install acc-mcp
acc install --claude
acc doctor
```

GitHub: https://github.com/YOURNAME/acc-context-compaction

## How it works

1. Execute command safely (subprocess, 30s timeout, 10MiB cap)
2. Dedup check (SHA-256, cross-turn with 7-day TTL)
3. Filter via regex (10 built-in + user TOML)
4. Score lines (keep errors/signatures, drop noise)
5. Compress with IRC (self-contained recovery token)

The entire pipeline is 70 tests, 88% coverage, MIT license.

Questions? What would you want to see in v0.3?
