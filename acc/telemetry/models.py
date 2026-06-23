from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class RunLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    command: str
    raw_tokens: int
    output_tokens: int
    deduped: bool = False
    compression_ratio: float = 1.0
    session_id: Optional[str] = None
    memories_used: int = 0
    latency_ms: Optional[int] = None
