from acc.mcp.server import main
import sys

if __name__ == "__main__":
    if "--install-hooks" in sys.argv:
        from acc.cli.install_hooks import install
        install()
        sys.exit(0)
    if "--uninstall-hooks" in sys.argv:
        from acc.cli.install_hooks import uninstall
        uninstall()
        sys.exit(0)
    if "--help" in sys.argv:
        print("ACC Context Compaction MCP Server")
        print("Usage: acc-mcp [options]")
        sys.exit(0)
    main()
