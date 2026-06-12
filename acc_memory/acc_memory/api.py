from fastapi import FastAPI
from pydantic import BaseModel
from .db import get_session
from .models import Container, Memory

app = FastAPI()

class Fact(BaseModel):
    subject: str
    predicate: str
    object: str
    scope: str
    kind: str = "fact"
    valid_from: str | None = None
    valid_until: str | None = None
    confidence: float = 0.8

@app.post("/memory/save")
def memory_save(container_key: str, facts: list[Fact]):
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
    return {"status": "ok"}

@app.get("/memory/search")
def memory_search(container_key: str, query: str):
    # TODO: implement hybrid semantic + keyword search
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
