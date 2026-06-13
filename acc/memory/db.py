import os
from sqlmodel import SQLModel, create_engine, Session

# We allow overriding the database URL for tests (e.g., sqlite:///:memory:)
DATABASE_URL = os.environ.get("ACC_DATABASE_URL", "sqlite:///acc_memory.db")

# Use check_same_thread=False for SQLite
engine = create_engine(
    DATABASE_URL, 
    echo=os.environ.get("ACC_DB_ECHO", "False").lower() in ("true", "1"),
    connect_args={"check_same_thread": False},
)

# Enable WAL for concurrent access from multiple Cursor sessions
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

def get_session():
    with Session(engine) as session:
        yield session
