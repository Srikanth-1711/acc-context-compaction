from datetime import datetime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, ForeignKey

Base = declarative_base()

class Container(Base):
    __tablename__ = "containers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, unique=True, index=True)
    kind: Mapped[str] = mapped_column(String)  # user | project | service
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    container_id: Mapped[int] = mapped_column(ForeignKey("containers.id"), index=True)
    subject: Mapped[str] = mapped_column(String, index=True)
    predicate: Mapped[str] = mapped_column(String)
    object: Mapped[str] = mapped_column(String)
    scope: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
