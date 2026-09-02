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
        self.model_path = (model_path or settings.model_file).expanduser().resolve()
        self.model = None
        self.error = None
        self.device = "cpu"
        diagnostics = self._diagnose_model_path()
        logger.info("Model diagnostic: %s", diagnostics)
        if diagnostics["error"]:
            self.error = diagnostics["error"]
            logger.warning("Custom detector is unavailable: %s", diagnostics["message"])
            return
        try:
            import torch
            from ultralytics import YOLO

            if torch.cuda.is_available():
                self.device = 0
                logger.info("CUDA available; using device=0 (%s)", torch.cuda.get_device_name(0))
            else:
                logger.warning("CUDA unavailable; using CPU")
            self.model = YOLO(str(self.model_path))
            names = self.model.names
            logger.info(
                "Loaded YOLO model path=%s type=%s task=%s class_names=%s number_of_classes=%s device=%s",
                self.model_path, type(self.model).__name__, getattr(self.model, "task", "unknown"),
                names, len(names), self.device,
            )
            if len(names) != len(settings.supported_classes) or any(
                names.get(class_id, "").casefold() != label.casefold()
                for class_id, label in settings.supported_classes.items()
            ):
                logger.warning(
                    "Model class metadata does not exactly match the configured four-class mapping: %s",
                    names,
                )
        except PermissionError as exc:
            self.error = "MODEL_PERMISSION_DENIED"
            logger.exception("Model file cannot be read due to insufficient permissions: %s", exc)
        except Exception as exc:
            self.error = "MODEL_INVALID"
            logger.exception("Invalid or unsupported YOLO model at %s: %s", self.model_path, exc)

    def _diagnose_model_path(self) -> dict[str, object]:
        diagnostics = {
            "path": str(self.model_path),
            "exists": self.model_path.exists(),
            "is_file": self.model_path.is_file(),
            "size": self.model_path.stat().st_size if self.model_path.exists() and self.model_path.is_file() else 0,
            "readable": False,
            "error": None,
            "message": "Model path is ready",
        }
        if not diagnostics["exists"]:
            diagnostics["error"] = "MODEL_NOT_FOUND"
            diagnostics["message"] = f"Model file not found: {self.model_path}"
            return diagnostics
        if not diagnostics["is_file"]:
            diagnostics["error"] = "MODEL_PATH_DIRECTORY"
            diagnostics["message"] = f"Model path points to a directory, not a .pt file: {self.model_path}"
            return diagnostics
        try:
            with self.model_path.open("rb"):
                diagnostics["readable"] = True
        except PermissionError:
            diagnostics["error"] = "MODEL_PERMISSION_DENIED"
            diagnostics["message"] = f"Model file cannot be read due to insufficient permissions: {self.model_path}"
        except OSError as exc:
            diagnostics["error"] = "MODEL_UNREADABLE"
            diagnostics["message"] = f"Model file cannot be opened: {self.model_path} ({exc})"
        return diagnostics

    @property
    def available(self) -> bool: return self.model is not None

    def detect(self, image: np.ndarray) -> list[dict]:
        if not self.model:
            messages = {
                "MODEL_NOT_FOUND": f"Model file not found: {self.model_path}",
                "MODEL_PATH_DIRECTORY": f"Model path points to a directory, not a .pt file: {self.model_path}",
                "MODEL_PERMISSION_DENIED": f"Model file cannot be read due to insufficient permissions: {self.model_path}",
                "MODEL_UNREADABLE": f"Model file cannot be opened: {self.model_path}",
                "MODEL_INVALID": f"Invalid or unsupported YOLO model: {self.model_path}. See the application log for details.",
            }
            code = self.error or "MODEL_INVALID"
            raise ModelUnavailableError(code, messages.get(code, "The trained marine-debris YOLO model could not be loaded. See the application log for details."))
        results = self.model.predict(image, device=self.device, verbose=False)
        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = settings.supported_classes.get(class_id)
                if class_name is None:
                    logger.warning("Ignoring unsupported model class id=%s name=%s", class_id, result.names.get(class_id, "unknown"))
                    continue
                detections.append({"class_name": class_name, "confidence": float(box.conf[0]), "bbox": [float(value) for value in box.xyxy[0]]})
        return detections


class DemoDetector:
    def detect(self, image: np.ndarray) -> list[dict]:
        height, width = image.shape[:2]
        return [{"class_name": "Shipwreck", "confidence": 0.88, "bbox": [width * .28, height * .30, width * .52, height * .56]}, {"class_name": "Mine", "confidence": 0.76, "bbox": [width * .62, height * .58, width * .86, height * .72]}]
