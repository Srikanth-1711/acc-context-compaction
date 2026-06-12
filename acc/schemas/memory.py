from pydantic import BaseModel
from typing import List

class Fact(BaseModel):
    subject: str
    predicate: str
    object: str
    scope: str
    kind: str = "fact"
    valid_from: str | None = None
    valid_until: str | None = None
    confidence: float = 0.8

class MemoryCreate(BaseModel):
    container_key: str
    facts: List[Fact]

class MemorySearch(BaseModel):
    container_key: str
    query: str
