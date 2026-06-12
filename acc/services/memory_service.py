from acc.schemas.memory import MemoryCreate, MemorySearch
from acc.memory.repositories import MemoryRepository

def save_memory(data: MemoryCreate):
    repo = MemoryRepository()
    repo.save(data.container_key, data.facts)
    return {"status": "ok"}

def search_memory(data: MemorySearch):
    repo = MemoryRepository()
    return repo.search(data.container_key, data.query)
