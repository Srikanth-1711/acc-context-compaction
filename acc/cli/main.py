import sys

def main():
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
    
    # Only AFTER checking flags, start MCP server
    from acc.mcp.server import run
    run()

if __name__ == "__main__":
    main()
