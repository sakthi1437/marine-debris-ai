def filter_detections(detections: list[dict], image_width: int, image_height: int, threshold: float = .70, min_size: int = 8) -> list[dict]:
    accepted = []
    for detection in detections:
        x1, y1, x2, y2 = detection["bbox"]
        width, height = x2 - x1, y2 - y1
        if detection["confidence"] < threshold or x1 < 0 or y1 < 0 or x2 > image_width or y2 > image_height or width < min_size or height < min_size or x2 <= x1 or y2 <= y1:
            continue
        detection = {**detection, "width": width, "height": height, "final_confidence": round(float(detection["confidence"]), 3), "filtering_status": "accepted"}
        accepted.append(detection)
    return accepted
