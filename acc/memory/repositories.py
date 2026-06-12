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
                
            for f in facts:
                m = Memory(
                    container_id=container.id,
                    subject=f.subject,
                    predicate=f.predicate,
                    object=f.object,
                    scope=f.scope,
                    kind=f.kind,
                    confidence=f.confidence,
                )
                session.add(m)
            session.commit()

    def search(self, container_key: str, query: str):
        with Session(engine) as session:
            statement = select(Container).where(Container.key == container_key)
            container = session.exec(statement).first()
            if not container:
                return []
                
            # Basic retrieval for now
            statement = select(Memory).where(Memory.container_id == container.id).order_by(Memory.created_at.desc()).limit(50)
            memories = session.exec(statement).all()
            
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
