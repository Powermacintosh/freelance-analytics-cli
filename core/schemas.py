from pydantic import BaseModel, Field
from typing import List, Optional


class AvgHourlyRateByInput(BaseModel):
    by: str = Field(description='Группировка: category, region, experience, platform, project_type')
class AvgSuccessRateByInput(BaseModel):
    by: str = Field(description='Группировка: category, region, experience, platform, project_type')
class AvgClientRatingByInput(BaseModel):
    by: str = Field(description='Группировка: category, region, experience, platform, project_type')
class AvgMarketingSpendByInput(BaseModel):
    by: str = Field(description='Группировка: category, region, experience, platform, project_type')

class BatchAnalyticsMethod(BaseModel):
    method: str
    by: Optional[str] = None

class BatchAnalyticsInput(BaseModel):
    methods: List[BatchAnalyticsMethod]