import os
import tempfile
from acc.filters.pipeline import FilterPipeline

def test_tee_failsafe():
    # Create 3000 lines of text
    lines = [f"Line {i}" for i in range(3000)]
    text = "\n".join(lines)
    
    # Profile with max_lines = 100
    profile = {"max_lines": 100, "head_ratio": 0.5, "type": "text"}
    pipeline = FilterPipeline(profile)
    
    out = pipeline.execute(text)
    
    # It should have truncated and added the failsafe message
    assert "Truncated to save tokens. Full raw output saved to" in out
    
    # Extract the log path
    import re
    match = re.search(r"saved to (.*?)\. Use view_file", out)
    assert match is not None
    log_path = match.group(1)
    
    assert os.path.exists(log_path)
    
    with open(log_path, "r", encoding="utf-8") as f:
        raw_out = f.read()
        
    assert len(raw_out.split("\n")) == 3000
    assert "Line 2999" in raw_out
    
    # Cleanup
    os.remove(log_path)
