import pytest
from sqlmodel import Session, create_engine, SQLModel
from acc.memory.retrieval import MemoryRetriever
from acc.memory.models import MemoryFact
import time

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_memory_save_and_temporal_contradiction(session: Session):
    retriever = MemoryRetriever(session)
    
    # Save a fact
    fact1 = retriever.save_fact("app.py", "imports", "os, sys")
    assert fact1.valid_until is None
    
    # Save a contradicting fact
    fact2 = retriever.save_fact("app.py", "imports", "os, sys, json")
    
    session.refresh(fact1)
    assert fact1.valid_until is not None  # Old fact is deprecated
    assert fact2.valid_until is None      # New fact is active
    
    # Temporal query
    active = retriever.temporal_query("app.py")
    assert len(active) == 1
    assert active[0].object == "os, sys, json"

def test_memory_keyword_search(session: Session):
    retriever = MemoryRetriever(session)
    retriever.save_fact("app.py", "imports", "fastapi, uvicorn")
    retriever.save_fact("models.py", "imports", "sqlmodel")
    
    results = retriever.keyword_search("fastapi")
    assert len(results) == 1
    assert results[0][0].subject == "app.py"
