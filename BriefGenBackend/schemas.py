from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AgentQuestion(BaseModel):
    id: str
    field: str
    text: str
    hint: str = ""
    required: bool = True

class AgentQuestionResponse(BaseModel):
    type: str  # "question" | "final"
    question: Optional[AgentQuestion] = None
    draft: Optional[Dict[str, Any]] = None
