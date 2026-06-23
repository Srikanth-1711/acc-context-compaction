import os
import time
import argparse
from pathlib import Path
from acc.mcp_server import mcp, acc_run

def benchmark():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", action="append", default=["git"])
    parser.add_argument("--output", default="benchmark_report.md")
    args = parser.parse_args()
    
    report = ["# ACC Benchmark Report", ""]
    
    for suite in args.suite:
        report.append(f"## Suite: {suite}")
        
        # We simulate running acc_run
        if suite == "git":
            cmd = "git"
            cmd_args = ["status"]
        elif suite == "cargo":
            cmd = "cargo"
            cmd_args = ["build"]
        elif suite == "pytest":
            cmd = "pytest"
            cmd_args = []
        else:
            cmd = suite
            cmd_args = []
            
        start_time = time.time()
        
        try:
            res = acc_run(cmd, cmd_args)
            latency = (time.time() - start_time) * 1000
            
            report.append(f"- **Command**: `{cmd} {' '.join(cmd_args)}`")
            report.append(f"- **Tokens Saved**: {res.get('tokens_saved', 0)}")
            report.append(f"- **Compression Ratio**: {res.get('compression_ratio', 1.0):.2f}")
            report.append(f"- **Deduped**: {res.get('deduped', False)}")
            report.append(f"- **Latency**: {latency:.2f} ms")
            report.append("")
        except Exception as e:
            report.append(f"- **Error**: {e}")
            report.append("")
            
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Benchmark completed. Report saved to {args.output}")

if __name__ == "__main__":
    benchmark()
