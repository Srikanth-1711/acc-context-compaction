# ACC Context Compaction - Installation & Configuration

ACC provides multiple packaging formats to support any environment—from local JS developers to locked-down enterprise machines and CI/CD pipelines.

---

## 1. NPX (Zero-Install JS/TS)

The NPX wrapper automatically downloads a pre-compiled OS-specific binary from GitHub Releases on the first run and caches it in `~/.acc-mcp/bin/`. No Python installation is required.

### Configuration Snippets

**Claude Desktop (`claude_desktop_config.json`)**
```json
{
  "mcpServers": {
    "acc": {
      "command": "npx",
      "args": ["-y", "acc-mcp"]
    }
  }
}
```

**Cursor / Windsurf / Cline / Continue.dev**
Use standard MCP configuration pointing to `npx` with args `-y acc-mcp`.

---

## 2. Python PIP (Development)

The standard installation method for Python environments.

### Configuration Snippets

**Claude Desktop (`claude_desktop_config.json`)**
```json
{
  "mcpServers": {
    "acc": {
      "command": "acc-mcp",
      "args": []
    }
  }
}
```
*(Ensure `acc-mcp` is in your PATH, or provide the absolute path to the executable).*

---

## 3. Standalone Binary (PyInstaller)

For locked machines without `pip` or Node access. Download the binary for your OS directly from GitHub Releases (`acc-mcp-windows-x64.exe`, `acc-mcp-linux-x64`, etc.).

### Configuration Snippets

**Claude Desktop / Cursor / Windsurf**
```json
{
  "mcpServers": {
    "acc": {
      "command": "/absolute/path/to/acc-mcp-windows-x64.exe",
      "args": []
    }
  }
}
```

---

## 4. Docker (CI/CD & Server)

The Docker image supports both STDIO mode (for agents) and REST API mode (for pipelines).

### Configuration Snippets

**Claude Desktop / Cursor (STDIO Mode)**
```json
{
  "mcpServers": {
    "acc": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "acc-mcp"]
    }
  }
}
```

**REST API Mode (docker-compose.yml)**
```yaml
version: '3.8'
services:
  acc-mcp-api:
    image: acc-mcp
    ports:
      - "8000:8000"
    command: ["uvicorn", "acc.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Known Limitations

1. **NPX Wrapper**: Requires outbound internet access to `github.com` on the first run to download the binary.
2. **Standalone Binary**: Large file size (~30MB+) due to bundled Python runtime and Tree-sitter C extensions.
3. **Docker (STDIO)**: Mounting local directories is required if you want ACC to slice files on your host machine. Add `-v /path/to/repo:/repo` to the Docker run args.
