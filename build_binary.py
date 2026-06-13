import subprocess
import sys
import os

def build():
    print("Building Standalone ACC Binary...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "acc-mcp",
        "--collect-all", "tree_sitter_languages",
        "--collect-all", "tree_sitter",
        "--collect-all", "mcp",
        "--copy-metadata", "tree_sitter_languages",
        "main.py"
    ]
    
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("Build failed")
        sys.exit(1)
        
    print("Build complete. Running smoke test...")
    binary_name = "acc-mcp.exe" if os.name == "nt" else "acc-mcp"
    binary_path = os.path.join("dist", binary_name)
    
    smoke_res = subprocess.run([binary_path, "--help"], capture_output=True, text=True)
    if smoke_res.returncode != 0:
        print("Binary build failed (smoke test returned non-zero)")
        print("\n".join(smoke_res.stderr.splitlines()[-20:]))
        sys.exit(1)
        
    print("Build and smoke test successful!")

if __name__ == "__main__":
    build()
