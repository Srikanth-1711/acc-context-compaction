from typing import List

# Default list of noise prefixes
DEFAULT_NOISE_PREFIXES = [
    "INFO  ", 
    "DEBUG ", 
    "TRACE ", 
    "[INFO]", 
    "[DEBUG]",
    "progress:",
    "downloading",
    "extracting"
]

def remove_noise(lines: List[str], custom_patterns: List[str] = None, 
                 important_patterns: List[str] = None) -> List[str]:
    """
    Strips universally useless lines, plus any custom noise patterns provided.
    """
    patterns = custom_patterns if custom_patterns is not None else DEFAULT_NOISE_PREFIXES
    out = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Important patterns override noise removal
        if important_patterns:
            is_important = any(p.lower() in stripped.lower() for p in important_patterns)
            if is_important:
                out.append(line)
                continue
        
        is_noise = False
        lower_line = stripped.lower()
        
        for pattern in patterns:
            # Simple substring match for flexibility
            if pattern.lower() in lower_line:
                is_noise = True
                break
                
        if not is_noise:
            out.append(line)
            
    return out
