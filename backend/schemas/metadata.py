from datetime import datetime
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    survey_id: str = "SURVEY_SAMPLE"
    ping_id: str | None = None
    latitude: float = Field(0, ge=-90, le=90)
    longitude: float = Field(0, ge=-180, le=180)
    timestamp: datetime | None = None
    source: str = "simulated"
