import sys
import os

def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "install"
    
    if action == "install":
        from acc.cli.install_hooks import install
        install()
    elif action == "uninstall":
        from acc.cli.install_hooks import uninstall
        uninstall()
    else:
        print(f"Usage: acc-hooks install|uninstall")
        sys.exit(1)

if __name__ == "__main__":
    main()
