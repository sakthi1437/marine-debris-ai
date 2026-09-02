def score_detection(detection: dict) -> tuple[float, str]:
    confidence = float(detection["final_confidence"])
    area = detection["width"] * detection["height"]
    size_factor = min(1.0, max(.5, area / 10000))
    score = round(confidence * (.8 + .2 * size_factor), 3)
    return score, "HIGH" if score >= .85 else "MEDIUM" if score >= .70 else "LOW"
