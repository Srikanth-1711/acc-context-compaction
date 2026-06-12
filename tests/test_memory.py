import pytest
from sqlmodel import SQLModel, create_engine, Session
from acc.memory.models import Container, Memory
from acc.schemas.memory import Fact
from acc.memory.repositories import MemoryRepository

from unittest.mock import patch

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with patch("acc.memory.repositories.engine", engine):
        with Session(engine) as session:
            yield session

def test_memory_crud(session: Session):
    repo = MemoryRepository()
    
    # Save facts
    facts = [
        Fact(subject="User", predicate="prefers", object="Python", scope="global")
    ]
    repo.save("test_container", facts)
    
    # Search facts
    results = repo.search("test_container", "Python")
    assert len(results) == 1
    assert results[0]["subject"] == "User"
    assert results[0]["object"] == "Python"
    
    # Empty search
    empty = repo.search("unknown_container", "query")
    assert len(empty) == 0
