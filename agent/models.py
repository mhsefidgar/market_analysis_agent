from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class AnalysisRequest(BaseModel):
    product_name: str = Field(..., description="The name of the product to analyze")
    competitors: Optional[List[str]] = Field(default=[], description="List of competitor products")
    market_segment: Optional[str] = Field(default=None, description="Target market segment")

class AnalysisStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentResponse(BaseModel):
    report: str
    tool_calls_made: int
