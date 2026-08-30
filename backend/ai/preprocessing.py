from io import BytesIO
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def validate_image(data: bytes, filename: str, max_size: int) -> tuple[int, int]:
    if not data or len(data) > max_size:
        raise ValueError("Image is missing or exceeds the upload size limit")
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported image format")
    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            return image.width, image.height
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid image") from exc


def preprocess_image(data: bytes, denoise: bool = True, max_dimension: int = 1600) -> tuple[np.ndarray, int, int]:
    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Unable to decode image")
    original_height, original_width = image.shape[:2]
    scale = min(1.0, max_dimension / max(original_width, original_height))
    if scale < 1:
        image = cv2.resize(image, (int(original_width * scale), int(original_height * scale)), interpolation=cv2.INTER_AREA)
    if denoise:
        image = cv2.GaussianBlur(image, (3, 3), 0)
    return cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX), original_width, original_height
