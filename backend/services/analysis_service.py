import json
import logging
import time
import uuid
from pathlib import Path
import cv2
from backend.ai.anomaly_scoring import score_detection
from backend.ai.filtering import filter_detections
from backend.ai.preprocessing import preprocess_image, validate_image
from backend.ai.visualization import annotate
from backend.ai.yolo_detector import DemoDetector, YoloDetector
from backend.core.config import settings
from backend.database.repository import AnomalyRepository
from backend.geo.geotagger import geotag
from backend.schemas.metadata import Metadata

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def analyze(data: bytes, filename: str, metadata: Metadata, repository: AnomalyRepository, demo: bool = False) -> dict:
    started = time.perf_counter()
    max_size = settings.max_upload_size_mb * 1024 * 1024
    width, height = validate_image(data, filename, max_size)
    analysis_id = uuid.uuid4().hex
    safe_name = f"{analysis_id}_{Path(filename).name.replace(' ', '_')}"
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True); (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    original_path = DATA_DIR / "uploads" / safe_name
    processed_path = DATA_DIR / "processed" / f"{analysis_id}_processed.png"
    annotated_path = DATA_DIR / "processed" / f"{analysis_id}.png"
    original_path.write_bytes(data)
    processed, _, _ = preprocess_image(data)
    cv2.imwrite(str(processed_path), processed)
    detector = DemoDetector() if demo else YoloDetector()
    raw = detector.detect(processed)
    detections = filter_detections(raw, processed.shape[1], processed.shape[0], settings.confidence_threshold)
    latitude, longitude, source = geotag(metadata)
    output = []
    for detection in detections:
        final_confidence, priority = score_detection(detection)
        detection["final_confidence"] = final_confidence; detection["priority"] = priority
        item = repository.create({"survey_id": metadata.survey_id if metadata.survey_id != "SURVEY_SAMPLE" else analysis_id, "image_name": filename, "object_type": detection["class_name"], "model_confidence": detection["confidence"], "final_confidence": final_confidence, "priority": priority, "latitude": latitude, "longitude": longitude, "x1": detection["bbox"][0], "y1": detection["bbox"][1], "x2": detection["bbox"][2], "y2": detection["bbox"][3], "width": detection["width"], "height": detection["height"], "metadata_source": source})
        output.append({"id": item.id, "object_type": item.object_type, "model_confidence": item.model_confidence, "final_confidence": item.final_confidence, "priority": item.priority, "latitude": item.latitude, "longitude": item.longitude, "metadata_source": item.metadata_source, "bbox": {"x1": item.x1, "y1": item.y1, "x2": item.x2, "y2": item.y2}, "width": item.width, "height": item.height})
    annotated = annotate(processed, detections)
    cv2.imwrite(str(annotated_path), annotated)
    elapsed = int((time.perf_counter() - started) * 1000)
    logger.info("Analysis %s completed in %sms with %s detections", analysis_id, elapsed, len(output))
    survey_id = metadata.survey_id if metadata.survey_id != "SURVEY_SAMPLE" else analysis_id
    return {"analysis_id": analysis_id, "survey_id": survey_id, "status": "completed", "mode": "demo" if demo else "ai", "processing_time_ms": elapsed, "image": {"filename": filename, "width": width, "height": height, "original_path": str(original_path), "processed_path": str(processed_path), "annotated_path": str(annotated_path), "annotated_url": f"/api/images/{analysis_id}"}, "detections": output, "message": "DEMO / SAMPLE DATA" if demo else None}
