import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

DB_PATH = os.getenv("BRIEFGEN_DB") or os.path.join(os.path.dirname(__file__), "..", "briefgen.db")
DB_URI = f"sqlite:///{os.path.abspath(DB_PATH)}"

connect_args = {"check_same_thread": False}
engine = create_engine(DB_URI, echo=False, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))

def get_session():
    with Session(engine) as session:
        yield session
