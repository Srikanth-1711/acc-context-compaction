import re

ANSI_ESCAPE_PATTERN = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')

def strip_ansi(lines: list[str]) -> list[str]:
    """Removes ANSI escape codes (color codes, terminal formatting) from the input lines."""
    return [ANSI_ESCAPE_PATTERN.sub('', line) for line in lines]
