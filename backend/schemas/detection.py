from pydantic import BaseModel


class BBox(BaseModel):
    x1: float; y1: float; x2: float; y2: float


class DetectionResponse(BaseModel):
    id: int | None = None
    object_type: str
    model_confidence: float
    final_confidence: float
    priority: str
    latitude: float
    longitude: float
    metadata_source: str
    bbox: BBox
    width: float
    height: float
