def head_tail(lines: list[str], max_lines: int = 1000, head_ratio: float = 0.2) -> list[str]:
    """
    Limits the output to a maximum number of lines, preserving a portion from the head
    and the remainder from the tail.
    """
    if len(lines) <= max_lines:
        return lines
        
    head_count = int(max_lines * head_ratio)
    tail_count = max_lines - head_count
    
    head_lines = lines[:head_count]
    tail_lines = lines[-tail_count:]
    
    return head_lines + [f"... truncated {len(lines) - max_lines} lines ..."] + tail_lines
