from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MemoryFact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    predicate: str
    object: str
    scope: str = Field(default="global")
    kind: str = Field(default="fact")
    valid_from: datetime = Field(default_factory=_utc_now)
    valid_until: Optional[datetime] = None

