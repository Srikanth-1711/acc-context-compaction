from pydantic import BaseModel
from typing import List, Dict

class CompactionRequest(BaseModel):
    cmd: List[str]
    cwd: str = "."
    hint: str = ""

class CompactionResponse(BaseModel):
    text: str
