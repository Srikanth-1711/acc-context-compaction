from acc.memory.models import Container, Memory
from acc.memory.db import get_session
from acc.schemas.memory import Fact

class MemoryRepository:
    def save(self, container_key: str, facts: list[Fact]):
        with get_session() as session:
            container = (
                session.query(Container)
                .filter(Container.key == container_key)
                .one_or_none()
            )
            if not container:
                container = Container(key=container_key, kind="project")
                session.add(container)
                session.flush()
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
        # Stub for search
        with get_session() as session:
            container = (
                session.query(Container)
                .filter(Container.key == container_key)
                .one_or_none()
            )
            if not container:
                return []
            memories = (
                session.query(Memory)
                .filter(Memory.container_id == container.id)
                .order_by(Memory.created_at.desc())
                .limit(50)
                .all()
            )
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
