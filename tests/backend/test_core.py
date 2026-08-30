from io import BytesIO
from PIL import Image
from fastapi.testclient import TestClient
from backend.ai.anomaly_scoring import score_detection
from backend.ai.filtering import filter_detections
from backend.ai.preprocessing import preprocess_image, validate_image
from backend.main import app


def image_bytes():
    image = Image.new("L", (320, 200), 100); stream = BytesIO(); image.save(stream, format="PNG"); return stream.getvalue()


def test_image_validation_and_preprocessing():
    data = image_bytes()
    assert validate_image(data, "sonar.png", 1_000_000) == (320, 200)
    processed, width, height = preprocess_image(data)
    assert processed.shape == (200, 320) and (width, height) == (320, 200)


def test_filter_and_score():
    detections = filter_detections([{"class_name": "pipe", "confidence": .9, "bbox": [10, 10, 100, 80]}, {"class_name": "debris", "confidence": .2, "bbox": [0, 0, 30, 30]}], 320, 200)
    assert len(detections) == 1
    score, priority = score_detection(detections[0])
    assert score > .7 and priority in {"HIGH", "MEDIUM"}


def test_health_and_demo_analysis():
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    response = client.post("/api/demo/run", files={"file": ("sonar.png", image_bytes(), "image/png")}, data={"metadata": '{"survey_id":"DEMO_001","latitude":9.9,"longitude":78.1,"source":"simulated"}'})
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "demo" and body["message"] == "DEMO / SAMPLE DATA" and len(body["detections"]) == 2


def test_invalid_image_rejected():
    response = TestClient(app).post("/api/demo/run", files={"file": ("bad.png", b"nope", "image/png")})
    assert response.status_code == 400


def test_ai_mode_reports_missing_model():
    response = TestClient(app).post("/api/analyze", files={"file": ("sonar.png", image_bytes(), "image/png")})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "MODEL_NOT_FOUND"
