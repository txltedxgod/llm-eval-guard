from pydantic import BaseModel, Field
from typing import List

class GuardCheckRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=20000)

class GuardCheckResponse(BaseModel):
    is_safe: bool
    risk_score: float
    violations: List[str]
    masked_prompt: str
