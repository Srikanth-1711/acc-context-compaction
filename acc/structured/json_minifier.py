import json
from typing import Any

def truncate_depth(data: Any, current_depth: int, max_depth: int) -> Any:
    if current_depth > max_depth:
        if isinstance(data, dict):
            return {"...": "truncated"}
        elif isinstance(data, list):
            return ["... truncated ..."]
        else:
            return data
            
    if isinstance(data, dict):
        return {k: truncate_depth(v, current_depth + 1, max_depth) for k, v in data.items()}
    elif isinstance(data, list):
        return [truncate_depth(item, current_depth + 1, max_depth) for item in data]
    else:
        return data

def compress_json(json_str: str, max_depth: int = -1) -> str:
    """
    Minifies a JSON string and optionally truncates objects/arrays deeper than max_depth.
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return json_str
        
    if max_depth >= 0:
        data = truncate_depth(data, 0, max_depth)
        
    # Minify
    return json.dumps(data, separators=(',', ':'))
