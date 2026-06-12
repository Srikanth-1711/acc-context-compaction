from fastapi import FastAPI
from acc.schemas.memory import MemoryCreate, MemorySearch
from acc.services.memory_service import save_memory, search_memory

app = FastAPI(title="ACC API")

@app.post("/memory/save")
def api_memory_save(data: MemoryCreate):
    return save_memory(data)

@app.post("/memory/search")
def api_memory_search(data: MemorySearch):
    return search_memory(data)
