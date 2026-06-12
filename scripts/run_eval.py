from acc.evals.harness import EvaluationHarness

def identity_filter(text: str) -> str:
    # 0% compression, 100% signal preservation
    return text

def aggressive_filter(text: str) -> str:
    # 100% compression, 0% signal preservation
    return ""

def good_filter(text: str) -> str:
    # Keeps only lines with 'Error', 'Warning', or 'diff'
    # High compression, decent signal preservation
    lines = text.split("\n")
    kept = [l for l in lines if "Error" in l or "WARNING" in l or "diff" in l or "assert" in l or "return" in l or "file" in l]
    return "\n".join(kept)

if __name__ == "__main__":
    harness = EvaluationHarness("benchmarks")
    
    print("--- Identity Filter (No Compression) ---")
    res = harness.evaluate_filter(identity_filter, "pytest")
    print(res)
    
    print("\n--- Aggressive Filter (Full Compression) ---")
    res = harness.evaluate_filter(aggressive_filter, "pytest")
    print(res)
    
    print("\n--- Good Filter (Signal Preservation) ---")
    res = harness.evaluate_filter(good_filter, "pytest")
    print(res)
