# ACC - Automatically Context Compaction

## Project Overview
ACC is a context compaction framework designed to drastically reduce token consumption and improve context retention for AI IDEs and agents. It contains three main modules:

1. **`acc_cli`**: A Python-based CLI proxy that intelligently filters, deduplicates, and compresses verbose terminal outputs (such as massive git logs or test runner failures) before sending them to the LLM.
2. **`acc_memory`**: A FastAPI and SQLAlchemy-powered memory backend for durable, cross-session context retention. It extracts semantic facts from conversations and stores them.
3. **`acc_mcp`**: A standard Model Context Protocol (MCP) server that seamlessly exposes both the CLI proxy and the memory backend tools to modern IDEs like Cursor and Codex.

## Key Features
- **Token Efficiency:** Drops terminal output token usage by 50-80% using deterministic heuristic filtering without relying on expensive LLM summaries.
- **Tee Failsafe Strategy:** When logs are aggressively truncated, the full raw output is safely dumped to a local temporary file, and a footnote is provided so the AI can retrieve the rest of the file if needed.
- **Fact-Based Memory:** Converts passive conversational history into an atomic, queryable knowledge graph to prevent context amnesia across large repositories.
- **Smart Git Parsers:** Contains built-in interceptors for `git status`, `git diff`, and `git log` to strip out noise and condense the output format specifically for LLM ingestion.

## Architecture & Integration
ACC is designed as a standalone toolchain. Once the MCP server is mounted in your IDE, the AI is instructed (via system prompts) to execute all shell commands through the `acc.cli_run` tool rather than running raw terminal processes.
