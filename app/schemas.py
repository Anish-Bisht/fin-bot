from pydantic import BaseModel
from typing import List, Optional

class BriefRequest(BaseModel):
    query: str
    thread_id: str

class BriefResponse(BaseModel):
    result: str
    route: str
    warnings: str
    sources: List[str]
    execution_time: float
    agent_thoughts: Optional[str] = ""