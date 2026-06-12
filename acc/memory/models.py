from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Container(SQLModel, table=True):
    __tablename__ = "containers"
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, index=True)
    kind: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Memory(SQLModel, table=True):
    __tablename__ = "memories"
    id: Optional[int] = Field(default=None, primary_key=True)
    container_id: int = Field(foreign_key="containers.id", index=True)
    subject: str = Field(index=True)
    predicate: str
    object: str
    scope: str = Field(index=True)
    kind: str
    valid_from: Optional[datetime] = Field(default=None)
    valid_until: Optional[datetime] = Field(default=None)
    confidence: float = Field(default=0.8)
    created_at: datetime = Field(default_factory=datetime.utcnow)
