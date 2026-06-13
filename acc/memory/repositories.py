from typing import List

from sqlmodel import Session, select
from acc.memory.models import Container, Memory
from acc.memory.db import engine
from acc.schemas.memory import Fact

class MemoryRepository:
    def save(self, container_key: str, facts: list[Fact]):
        with Session(engine) as session:
            statement = select(Container).where(Container.key == container_key)
            container = session.exec(statement).first()
            if not container:
                container = Container(key=container_key, kind="project")
                session.add(container)
                session.commit()
                session.refresh(container)
                
            from datetime import datetime
            
            for f in facts:
                # Check for temporal contradiction
                existing_stmt = select(Memory).where(
                    Memory.container_id == container.id,
                    Memory.subject == f.subject,
                    Memory.predicate == f.predicate,
                    Memory.valid_until.is_(None)
                )
                existing_mems = session.exec(existing_stmt).all()
                for old_mem in existing_mems:
                    if old_mem.object != f.object:
                        old_mem.valid_until = datetime.utcnow()
                        session.add(old_mem)
                
                m = Memory(
                    container_id=container.id,
                    subject=f.subject,
                    predicate=f.predicate,
                    object=f.object,
                    scope=f.scope,
                    kind=f.kind,
                    valid_from=datetime.utcnow(),
                    confidence=f.confidence,
                )
                session.add(m)
            session.commit()

    def search(
        self,
        container_key: str,
        query: str = "",
        limit: int = 50,
    ) -> list[dict]:
        with Session(engine) as session:
            # Get the container first
            container = session.exec(
                select(Container).where(
                    Container.key == container_key
                )
            ).first()

            if not container:
                return []

            # Base query for active facts
            stmt = select(Memory).where(
                Memory.container_id == container.id,
                Memory.valid_until.is_(None)
            )

            # Apply keyword filtering if query provided
            if query:
                # We need to fetch and filter in python because sqlite case-insensitive
                # LIKE on multiple fields dynamically is tricky with SQLModel
                all_facts = session.exec(stmt).all()
                query_tokens = query.lower().split()
                
                scored_facts = []
                for fact in all_facts:
                    text_blob = f"{fact.subject} {fact.predicate} {fact.object}".lower()
                    score = sum(1 for t in query_tokens if t in text_blob)
                    if score > 0:
                        scored_facts.append((score, fact))
                
                # Sort by score descending, then by created_at descending (recency)
                scored_facts.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
                memories = [f[1] for f in scored_facts[:limit]]
            else:
                # Just get the most recent ones
                stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
                memories = session.exec(stmt).all()

            return [
                {
                    "subject": m.subject,
                    "predicate": m.predicate,
                    "object": m.object,
                    "scope": m.scope,
                    "kind": m.kind,
                    "created_at": m.created_at.isoformat(),
                }
                for m in memories
            ]
