import json
from pathlib import Path


if __name__ == "__main__":
    output = Path("backend/data/demo"); output.mkdir(parents=True, exist_ok=True)
    payload = [{"survey_id": "DEMO_SURVEY_01", "ping_id": "PING_001", "latitude": 9.9252, "longitude": 78.1194, "source": "simulated"}, {"survey_id": "DEMO_SURVEY_02", "ping_id": "PING_002", "latitude": 10.01, "longitude": 78.2, "source": "simulated"}]
    (output / "metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote simulated demo metadata to {output / 'metadata.json'}")
