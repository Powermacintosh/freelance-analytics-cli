from pydantic import BaseModel
from typing import List, Optional


class BatchAnalyticsMethod(BaseModel):
    method: str
    by: Optional[str] = None

class BatchAnalyticsInput(BaseModel):
    methods: List[BatchAnalyticsMethod]