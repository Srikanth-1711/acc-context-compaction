# A list of standard prefixes or patterns that represent low-signal noise
NOISE_PREFIXES = [
    "INFO  ", 
    "DEBUG ", 
    "TRACE ", 
    "[INFO]", 
    "[DEBUG]",
    "progress:",
    "downloading",
    "extracting"
]

def remove_noise(lines: list[str]) -> list[str]:
    """
    Strips universally useless lines (e.g., empty whitespace, info logs, generic progress indicators).
    """
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        is_noise = False
        lower_line = stripped.lower()
        
        for prefix in NOISE_PREFIXES:
            if lower_line.startswith(prefix.lower()):
                is_noise = True
                break
                
        if not is_noise:
            out.append(line)
            
    return out
