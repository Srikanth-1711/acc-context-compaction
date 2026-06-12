import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from acc.memory.models import Container, Memory
from acc.memory.repositories import MemoryRepository
from acc.schemas.memory import Fact
from acc.memory import db

@pytest.fixture(autouse=True)
def setup_db():
    # Use an in-memory SQLite DB for tests instead of the real one
    db.engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(db.engine)
    from acc.memory import repositories
    repositories.engine = db.engine
    yield
    SQLModel.metadata.drop_all(db.engine)

def test_temporal_overrides():
    repo = MemoryRepository()
    
    # Save first fact
    fact1 = Fact(
        subject="Node.js",
        predicate="version",
        object="v16",
        scope="project",
        kind="tool"
    )
    repo.save("test_project", [fact1])
    
    # Search should return fact1
    res1 = repo.search("test_project", "node.js")
    assert len(res1) == 1
    assert res1[0]["object"] == "v16"
    
    # Save overriding fact
    fact2 = Fact(
        subject="Node.js",
        predicate="version",
        object="v20",
        scope="project",
        kind="tool"
    )
    repo.save("test_project", [fact2])
    
    # Search should ONLY return fact2, not fact1
    res2 = repo.search("test_project", "node.js")
    assert len(res2) == 1
    assert res2[0]["object"] == "v20"
    
    # Verify DB state directly: fact1 should have valid_until set
    with Session(db.engine) as session:
        memories = session.exec(select(Memory)).all()
        assert len(memories) == 2
        m1 = [m for m in memories if m.object == "v16"][0]
        m2 = [m for m in memories if m.object == "v20"][0]
        
        assert m1.valid_until is not None
        assert m2.valid_until is None
