from pydantic import BaseModel
from backend.schemas.detection import DetectionResponse


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    mode: str
    processing_time_ms: int
    image: dict
    detections: list[DetectionResponse]
    message: str | None = None
