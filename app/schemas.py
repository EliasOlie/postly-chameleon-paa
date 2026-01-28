from pydantic import BaseModel, Field
from typing import Dict, Any

class PaaRequest(BaseModel):
    content: str = Field(..., description="Conteúdo do post", max_length=15000)
    include_sponsored: bool = True

class PaaResponse(BaseModel):
    html_fragment: str 
    json_ld: Dict[str, Any]