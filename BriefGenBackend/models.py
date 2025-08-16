from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy import JSON as SAJSON
import uuid

def gen_id() -> str:
    return uuid.uuid4().hex

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Draft(SQLModel, table=True):
    id: str = Field(default_factory=gen_id, primary_key=True)
    template: str
    status: str = Field(default="collecting")
    answers_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(SAJSON))
    draft_json: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(SAJSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
