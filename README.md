# Underwater Marine Debris Intelligence

Hackathon prototype for side-scan sonar image analysis. The primary interface is a local PySide6 desktop tool. The pipeline validates and preprocesses an uploaded image, runs a custom YOLO detector when `backend/models/best.pt` exists, filters detections, calculates a clearly labeled prototype anomaly score, associates geographic metadata, stores anomalies in SQLite, and exports reports. FastAPI and the React client remain optional integration surfaces.

## Features

- Explicit `AI ANALYSIS` and `DEMO / SAMPLE DATA` modes
- OpenCV grayscale, resize, denoise, and normalization pipeline
- Configurable confidence threshold and safe upload handling
- SQLite anomaly repository, annotated images, statistics, CSV, and JSON reports
- Native PySide6 workstation with drag-and-drop input, original/processed/annotated viewers, results, exports, and history
- Explicit location providers for manual coordinates, metadata files, unavailable live GPS, and labeled demo simulation
- Dataset validation, training, validation, and simulated demo metadata scripts

## Setup

Requires Python 3.11+.

```powershell
python -m pip install -r requirements.txt
```

Launch the desktop tool from the repository root:

```powershell
python desktop_app.py
```

The optional API can still be started separately:

```powershell
uvicorn backend.main:app --reload
```

The desktop tool starts in clearly labeled DEMO MODE so it works without a trained model. Turn DEMO MODE off for real inference; without `backend/models/best.pt`, it reports `Marine debris AI model not installed.` and does not fabricate detections.

## API

`GET /health`, `POST /api/analyze`, `POST /api/demo/run`, `GET /api/demo/status`, `GET /api/detections`, `GET /api/detections/{id}`, `DELETE /api/detections/{id}`, `GET /api/statistics`, `GET /api/reports/{survey_id}/json`, `GET /api/reports/{survey_id}/csv`.

## Dataset and model

Place labeled YOLO data under `dataset/images/{train,val,test}` and `dataset/labels/{train,val,test}`. `dataset/data.yaml` declares five classes: ghost net, shipwreck, pipe, cylinder, and debris. Use `scripts/prepare_dataset.py`, then train with `scripts/train_model.py`. Put the resulting custom checkpoint at `backend/models/best.pt` and validate it with `scripts/validate_model.py`. No marine dataset is included or downloaded, and generic pretrained weights must not be described as a marine detector.

## Testing

```powershell
python -m pytest
```

Package a Windows executable when PyInstaller is installed:

```powershell
python -m pip install pyinstaller
pyinstaller --name MarineDebrisTool --windowed --onefile desktop_app.py
```

## Screenshots

Add project screenshots here when available.

## Limitations and future work

This is a prototype. The anomaly score is a heuristic and is not validated sonar physics. GPS values are never derived from pixels; they must be supplied as real, sample, or simulated metadata. A production system would require a curated labeled sonar dataset, calibrated navigation data, robust authentication, richer model evaluation, and operational monitoring.
