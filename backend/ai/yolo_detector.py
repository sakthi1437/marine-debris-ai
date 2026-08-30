import logging
from pathlib import Path
import numpy as np
from backend.core.config import settings

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class YoloDetector:
    def __init__(self, model_path: Path | None = None):
        self.model_path = model_path or settings.model_file
        self.model = None
        self.error = None
        if self.model_path.exists():
            try:
                from ultralytics import YOLO
                self.model = YOLO(str(self.model_path))
                logger.info("Loaded custom detector from %s", self.model_path)
            except Exception as exc:
                self.error = str(exc)
                logger.exception("Unable to load detector")
        else:
            self.error = "MODEL_NOT_FOUND"
            logger.warning("Custom detector is unavailable: %s", self.model_path)

    @property
    def available(self) -> bool: return self.model is not None

    def detect(self, image: np.ndarray) -> list[dict]:
        if not self.model:
            if self.error == "MODEL_NOT_FOUND":
                raise ModelUnavailableError("MODEL_NOT_FOUND", "The trained marine-debris YOLO model is unavailable. Select Demonstration Mode or install backend/models/best.pt.")
            raise ModelUnavailableError("MODEL_LOAD_FAILED", "The trained marine-debris YOLO model could not be loaded. Check the backend logs for details.")
        results = self.model.predict(image, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0]); names = result.names
                detections.append({"class_name": names.get(class_id, str(class_id)), "confidence": float(box.conf[0]), "bbox": [float(value) for value in box.xyxy[0]]})
        return detections


class DemoDetector:
    def detect(self, image: np.ndarray) -> list[dict]:
        height, width = image.shape[:2]
        return [{"class_name": "debris", "confidence": 0.88, "bbox": [width * .28, height * .30, width * .52, height * .56]}, {"class_name": "pipe", "confidence": 0.76, "bbox": [width * .62, height * .58, width * .86, height * .72]}]
