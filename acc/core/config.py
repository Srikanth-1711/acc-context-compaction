from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    dedup_window: int = 5
    max_lines: int = 400
    memory_base_url: str = "http://localhost:8001"
    
    class Config:
        env_prefix = "ACC_"

settings = Settings()
