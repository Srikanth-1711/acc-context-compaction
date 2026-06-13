from acc.mcp.server import main
import sys

if __name__ == "__main__":
    if "--help" in sys.argv:
        print("ACC Context Compaction MCP Server")
        print("Usage: acc-mcp [options]")
        sys.exit(0)
    main()
