from typing import Literal

from pydantic import BaseModel, Field


class AIClassificationRequest(BaseModel):
    issue: str = Field(min_length=3, max_length=4000)


class AIClassification(BaseModel):
    category: str
    subcategory: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    summary: str
    recommended_action: str

