from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select, func
from acc.memory.models import MemoryFact

class MemoryRetriever:
    def __init__(self, session: Session):
        self.session = session
    
    def save_fact(self, subject: str, predicate: str, object_value: str, scope: str = "global", kind: str = "fact") -> MemoryFact:
        """Saves a new fact and implements temporal contradiction detection."""
        # Find active facts with the same subject and predicate
        statement = select(MemoryFact).where(
            MemoryFact.subject == subject,
            MemoryFact.predicate == predicate,
            MemoryFact.valid_until == None
        )
        existing_facts = self.session.exec(statement).all()
        
        now = datetime.now(timezone.utc)
        for fact in existing_facts:
            if fact.object != object_value:
                # Contradiction detected, deprecate the old fact
                fact.valid_until = now
                self.session.add(fact)
            elif fact.object == object_value:
                # Identical fact exists, no need to duplicate
                return fact
                
        new_fact = MemoryFact(
            subject=subject,
            predicate=predicate,
            object=object_value,
            scope=scope,
            kind=kind,
            valid_from=now
        )
        self.session.add(new_fact)
        self.session.commit()
        self.session.refresh(new_fact)
        return new_fact
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[Tuple[MemoryFact, float]]:
        """Primitive keyword search as fallback."""
        tokens = query.lower().split()
        statement = select(MemoryFact).where(MemoryFact.valid_until == None)
        facts = self.session.exec(statement).all()
        
        scored = []
        for fact in facts:
            text = f"{fact.subject} {fact.predicate} {fact.object}"
            score = sum(1 for t in tokens if t in text.lower()) / len(tokens)
            if score > 0:
                scored.append((fact, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Tuple[MemoryFact, float]]:
        """Phase 2: Semantic search placeholder."""
        raise NotImplementedError("Install with `pip install acc-mcp[semantic]`")
    
    def temporal_query(self, subject: str, at_time: Optional[datetime] = None) -> List[MemoryFact]:
        """Query active facts for a subject at a given time."""
        at_time = at_time or datetime.now(timezone.utc)
        statement = select(MemoryFact).where(
            MemoryFact.subject == subject,
            MemoryFact.valid_from <= at_time,
            (MemoryFact.valid_until == None) | (MemoryFact.valid_until > at_time)
        )
        return self.session.exec(statement).all()
