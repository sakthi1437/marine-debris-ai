# PROJECT SPECIFICATION
# SIH ID26057 - AI-Powered Automated Underwater Marine Debris and Anomaly Detection System

You are the lead software architect, ML engineer, backend engineer, frontend engineer, QA engineer, and DevOps engineer for this project.

Your job is to BUILD THE COMPLETE WORKING PROTOTYPE in this repository.

Do not merely explain how to build it.

Inspect the repository, create the files, implement the application, install dependencies where appropriate, run tests, run builds, identify errors, fix them, and continue until the project is runnable.

============================================================
1. PROBLEM STATEMENT
============================================================

Problem Statement ID:
SIH26057

Title:
AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery

Objective:

Build an end-to-end software prototype that accepts side-scan sonar imagery and associated metadata, preprocesses the sonar image, detects man-made underwater debris/anomalies using an AI model, filters weak or noisy detections, assigns geographic metadata, stores the results, displays detections through an interactive dashboard, visualizes locations on a map, and generates structured anomaly reports.

The system should target objects such as:

- ghost nets
- shipwrecks
- pipes
- cylinders
- underwater debris

The system must be designed around the challenges of sonar imagery:

- speckle noise
- varying image resolution
- acoustic shadows
- natural seabed structures
- data quality issues
- vehicle motion effects

This is a HACKATHON PROTOTYPE.

Do not falsely claim scientific production-level accuracy.

============================================================
2. CORE PRODUCT
============================================================

The final application must implement this pipeline:

SONAR IMAGE
    ↓
UPLOAD
    ↓
IMAGE VALIDATION
    ↓
SONAR PREPROCESSING
    ↓
AI OBJECT DETECTION
    ↓
CONFIDENCE FILTERING
    ↓
ANOMALY SCORING
    ↓
OBJECT CLASSIFICATION
    ↓
GEOGRAPHIC METADATA ASSOCIATION
    ↓
DATABASE STORAGE
    ↓
DASHBOARD
    ↓
MAP
    ↓
CSV / JSON REPORT

============================================================
3. TECHNOLOGY STACK
============================================================

Backend:

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic
- SQLAlchemy
- SQLite
- OpenCV
- NumPy
- Pillow
- Pandas
- Ultralytics YOLO
- PyTorch
- python-multipart

Frontend:

- React
- Vite
- JavaScript
- Tailwind CSS
- Axios
- React-Leaflet
- Leaflet

Testing:

Backend:
- pytest
- pytest-asyncio
- FastAPI TestClient

Frontend:
- Vitest if practical

Code quality:

- ESLint
- Prettier
- Python type hints
- logging

Do not introduce:

- PostgreSQL
- Redis
- Kubernetes
- Docker
- microservices
- cloud infrastructure

unless explicitly required later.

Keep the prototype locally runnable.

============================================================
4. PROJECT STRUCTURE
============================================================

Create:

marine-debris-ai/

├── PROJECT_SPEC.md
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging_config.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   ├── detections.py
│   │   └── reports.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base_detector.py
│   │   ├── yolo_detector.py
│   │   ├── preprocessing.py
│   │   ├── filtering.py
│   │   ├── anomaly_scoring.py
│   │   └── visualization.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── geo/
│   │   ├── __init__.py
│   │   └── geotagger.py
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   └── generator.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── detection.py
│   │   ├── analysis.py
│   │   └── metadata.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── analysis_service.py
│   │
│   ├── models/
│   │   └── README.md
│   │
│   └── data/
│       ├── uploads/
│       ├── processed/
│       ├── results/
│       └── demo/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/
│       │   └── client.js
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── UploadPanel.jsx
│       │   ├── AnalysisStatus.jsx
│       │   ├── SonarViewer.jsx
│       │   ├── DetectionTable.jsx
│       │   ├── DetectionCard.jsx
│       │   ├── Statistics.jsx
│       │   ├── MapView.jsx
│       │   └── ReportControls.jsx
│       └── styles/
│           └── index.css
│
├── dataset/
│   ├── images/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── labels/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   └── data.yaml
│
├── scripts/
│   ├── prepare_dataset.py
│   ├── train_model.py
│   ├── validate_model.py
│   └── create_demo_data.py
│
└── tests/
    ├── backend/
    └── frontend/

Keep this structure modular.

============================================================
5. AI MODEL ARCHITECTURE
============================================================

Use YOLO through the Ultralytics Python API.

IMPORTANT:

Do NOT pretend that a generic pretrained YOLO model is trained to detect ghost nets, shipwrecks, pipes, cylinders, or marine debris.

The application must support a custom trained model.

Expected model location:

backend/models/best.pt

However, because the model may not initially exist, the application must gracefully handle:

MODEL_NOT_FOUND

without crashing the entire application.

Create a detector abstraction.

Example conceptual interface:

Detector.detect(image)

returns:

[
    {
        "class_name": "ghost_net",
        "confidence": 0.94,
        "bbox": {
            "x1": 100,
            "y1": 120,
            "x2": 350,
            "y2": 300
        }
    }
]

Do not hardcode fake detections in production inference code.

============================================================
6. SUPPORTED CLASSES
============================================================

Initial classes:

0: ghost_net
1: shipwreck
2: pipe
3: cylinder
4: debris

The architecture must allow additional classes later.

Store class names in configuration rather than scattering strings throughout the code.

============================================================
7. DEMO MODE
============================================================

Implement a clearly labeled DEMO MODE.

This is important because a custom marine sonar model or dataset may not be immediately available.

Demo Mode must:

- use local sample images
- use local sample metadata
- use clearly marked sample detections only if necessary
- never claim demo detections are actual AI predictions
- display "DEMO / SAMPLE DATA" prominently

Production/AI mode must use the actual detector.

The UI must clearly distinguish:

AI ANALYSIS

from:

DEMONSTRATION MODE

Never hide this distinction.

============================================================
8. IMAGE PREPROCESSING
============================================================

Implement:

- image validation
- supported file extensions
- image dimension validation
- grayscale conversion when appropriate
- resizing
- normalization
- configurable denoising
- contrast enhancement
- safe file handling

Do not overwrite the original image.

Preserve:

- original image
- processed image

Use OpenCV.

Make preprocessing configurable.

Create unit tests.

============================================================
9. CONFIDENCE FILTERING
============================================================

Implement a configurable confidence threshold.

Default:

0.70

Reject detections below threshold unless explicitly configured otherwise.

Implement:

- confidence threshold
- bounding box validation
- minimum object size
- maximum object size
- duplicate suppression
- invalid detection rejection

Return:

- model confidence
- final confidence
- filtering status

============================================================
10. ANOMALY SCORING
============================================================

Implement a prototype heuristic anomaly score.

The score may combine:

- model confidence
- bounding-box validity
- object size consistency
- shape-related heuristics
- optional acoustic-shadow-related heuristic

IMPORTANT:

Do not describe this as scientifically validated sonar physics.

Clearly label it:

"Prototype Anomaly Score"

Example:

model_confidence = 0.94

final_confidence = 0.91

priority = HIGH

Possible priorities:

HIGH
MEDIUM
LOW

Keep the scoring logic configurable.

============================================================
11. GEOTAGGING
============================================================

Metadata may look like:

{
    "survey_id": "SURVEY_001",
    "ping_id": "PING_001",
    "latitude": 9.9252,
    "longitude": 78.1194,
    "timestamp": "2026-08-26T12:00:00",
    "source": "sample"
}

Validate latitude:

-90 <= latitude <= 90

Validate longitude:

-180 <= longitude <= 180

Store:

metadata_source

with values such as:

- real
- sample
- simulated

Never claim simulated coordinates are real sonar navigation data.

Do not convert pixel coordinates into GPS coordinates without actual calibration/navigation metadata.

============================================================
12. DATABASE
============================================================

Use SQLite.

Use SQLAlchemy.

Create an anomalies table with:

- id
- survey_id
- image_name
- object_type
- model_confidence
- final_confidence
- priority
- latitude
- longitude
- x1
- y1
- x2
- y2
- width
- height
- metadata_source
- created_at

Create repository methods:

- create
- get
- list
- delete
- delete_by_survey
- count
- statistics

============================================================
13. FASTAPI API
============================================================

Create:

GET /health

POST /api/analyze

GET /api/detections

GET /api/detections/{id}

DELETE /api/detections/{id}

GET /api/statistics

GET /api/reports/{survey_id}/json

GET /api/reports/{survey_id}/csv

GET /api/demo/status

POST /api/demo/run

Use proper HTTP status codes.

Use Pydantic schemas.

Enable CORS for the local frontend.

Do not put business logic directly inside route handlers.

Use services.

============================================================
14. ANALYSIS PIPELINE
============================================================

POST /api/analyze must execute:

1. Validate upload
2. Generate unique analysis/survey ID
3. Save original image
4. Read optional metadata
5. Preprocess image
6. Run detector
7. Parse detections
8. Filter detections
9. Calculate anomaly score
10. Attach geographic metadata
11. Store results
12. Generate annotated image
13. Return structured response

Return:

{
    "analysis_id": "...",
    "status": "completed",
    "mode": "ai",
    "processing_time_ms": 1234,
    "image": {
        "filename": "...",
        "width": 1280,
        "height": 720
    },
    "detections": [...]
}

============================================================
15. ANNOTATED IMAGE
============================================================

Generate an annotated output image.

Draw:

- bounding boxes
- class name
- confidence
- priority

Example:

Ghost Net | 94% | HIGH

Do not modify the original image.

Provide an endpoint or static route for viewing the annotated result.

============================================================
16. FRONTEND
============================================================

Build a professional hackathon-quality dashboard.

Theme:

Marine scientific monitoring.

Use a clean dark/navy/white visual design but prioritize readability.

Do not overuse animations.

Dashboard sections:

HEADER

Title:
Underwater Marine Debris Intelligence

Subtitle:
AI-powered side-scan sonar anomaly detection

STATUS

- Backend status
- AI model status
- Mode: AI / DEMO

UPLOAD

- drag/drop area
- file picker
- metadata JSON option
- Analyze button

SONAR VIEWER

- original image
- annotated image
- bounding boxes
- detection selection

DETECTION PANEL

Columns:

Object
Confidence
Priority
Latitude
Longitude
Status

STATISTICS

- total anomalies
- high priority
- medium priority
- low priority
- ghost nets
- shipwrecks
- pipes
- cylinders
- debris

MAP

Use Leaflet + OpenStreetMap.

Show anomaly markers.

Clicking a marker should select the corresponding detection.

Clicking a detection should center the map.

REPORTS

Buttons:

Download CSV
Download JSON

============================================================
17. FRONTEND API CLIENT
============================================================

Use Axios.

Create one centralized API client.

Do not scatter hardcoded API URLs throughout components.

Use:

VITE_API_BASE_URL

from environment configuration.

Default development backend:

http://localhost:8000

============================================================
18. MAP
============================================================

Use React-Leaflet.

Base map:

OpenStreetMap.

Marker popup:

- object type
- confidence
- priority
- latitude
- longitude
- metadata source

If metadata source is sample/simulated, clearly display:

"Sample Coordinates"

============================================================
19. REPORTS
============================================================

CSV columns:

ID
Survey ID
Image
Object Type
Model Confidence
Final Confidence
Priority
Latitude
Longitude
X1
Y1
X2
Y2
Width
Height
Metadata Source
Created At

JSON should contain the same information.

============================================================
20. ERROR HANDLING
============================================================

Handle:

- invalid image
- oversized image
- missing image
- invalid metadata
- invalid coordinates
- missing AI model
- corrupted model
- inference failure
- database failure
- frontend/backend connection failure
- report generation failure

Show user-friendly errors.

Do not expose Python stack traces to normal users.

Log technical details on the backend.

============================================================
21. SECURITY
============================================================

Implement basic prototype security:

- validate uploaded file type
- limit upload size
- generate safe filenames
- prevent path traversal
- never execute uploaded files
- do not trust user-provided paths
- validate metadata
- avoid exposing internal filesystem paths

============================================================
22. TESTING
============================================================

Create tests for:

Backend:

- health endpoint
- image validation
- preprocessing
- metadata validation
- geotagging
- confidence filtering
- anomaly scoring
- database CRUD
- report generation
- API error handling

Frontend:

- upload component
- detection rendering
- statistics
- report controls

Where the actual model is unavailable, mock the detector in unit tests.

Do not require a trained model for ordinary unit tests.

============================================================
23. ENVIRONMENT CONFIGURATION
============================================================

Create:

.env.example

with:

APP_ENV=development
DATABASE_URL=sqlite:///./marine_debris.db
MODEL_PATH=backend/models/best.pt
CONFIDENCE_THRESHOLD=0.70
MAX_UPLOAD_SIZE_MB=20
VITE_API_BASE_URL=http://localhost:8000

Do not commit .env.

============================================================
24. REQUIREMENTS
============================================================

Create requirements.txt containing all backend dependencies.

Do not pin versions unnecessarily unless compatibility requires it.

After creating requirements.txt:

create the virtual environment if it does not exist.

Install dependencies.

If installation fails:

diagnose the actual error.

Do not randomly downgrade packages.

============================================================
25. FRONTEND SETUP
============================================================

Create the Vite React application.

Install:

- axios
- leaflet
- react-leaflet
- tailwind CSS or another lightweight styling solution

Ensure:

npm run build

works.

============================================================
26. README
============================================================

Create a complete README containing:

1. Project overview
2. Problem statement
3. Architecture
4. Features
5. Tech stack
6. Installation
7. Backend startup
8. Frontend startup
9. Dataset structure
10. Model setup
11. Demo mode
12. API endpoints
13. Screenshots placeholder section
14. Testing
15. Limitations
16. Future work

Clearly state that this is a prototype.

============================================================
27. DATASET SUPPORT
============================================================

Create dataset/data.yaml:

path: ./dataset

train: images/train
val: images/val
test: images/test

names:
  0: ghost_net
  1: shipwreck
  2: pipe
  3: cylinder
  4: debris

Create scripts for:

- dataset validation
- dataset preparation
- model training
- model validation

Do not download or fabricate a marine debris dataset automatically.

If a dataset is unavailable, keep the training pipeline ready and use Demo Mode.

============================================================
28. MODEL TRAINING
============================================================

Create:

scripts/train_model.py

It should accept configuration for:

- dataset YAML
- model
- epochs
- image size
- batch size
- device

Use a pretrained YOLO model as the initialization point when appropriate.

Do not claim the pretrained generic model detects marine debris.

The custom model must be trained on appropriately labeled sonar data before AI mode is considered valid.

============================================================
29. MODEL VALIDATION
============================================================

Create:

scripts/validate_model.py

Output:

- precision
- recall
- mAP where available
- class-level metrics
- validation summary

Make it clear that validation metrics depend on the actual dataset.

============================================================
30. DEMO DATA GENERATOR
============================================================

Create:

scripts/create_demo_data.py

Generate sample metadata files.

Do not generate fake scientific sonar data and call it real.

Demo metadata should clearly use:

"source": "simulated"

Create several sample locations and detection examples.

============================================================
31. UX
============================================================

The application must have these states:

EMPTY

No analysis yet.

UPLOADING

Uploading sonar data.

PROCESSING

AI analysis running.

SUCCESS

Analysis complete.

ERROR

Something failed.

MODEL MISSING

AI model unavailable.

DEMO

Demonstration mode active.

============================================================
32. ACCESSIBILITY
============================================================

Use:

- semantic HTML
- accessible buttons
- visible focus states
- meaningful labels
- alt text for images
- sufficient contrast

============================================================
33. PERFORMANCE
============================================================

Prototype priorities:

1. Correctness
2. Reliability
3. Clear UX
4. Reasonable performance

Do not implement premature optimization.

Resize very large images before inference.

Do not load huge images repeatedly into memory.

============================================================
34. LOGGING
============================================================

Backend should log:

- application startup
- analysis start
- analysis completion
- model loading
- inference duration
- detection count
- errors

Do not log sensitive uploaded data unnecessarily.

============================================================
35. DEVELOPMENT RULE
============================================================

You are operating as an autonomous coding agent.

Do not stop after generating a plan.

Actually implement the project.

Follow this order:

PHASE 1:
Repository inspection and scaffolding

PHASE 2:
Backend foundation

PHASE 3:
Database

PHASE 4:
Preprocessing

PHASE 5:
AI detector

PHASE 6:
Filtering and anomaly scoring

PHASE 7:
Geolocation

PHASE 8:
Analysis API

PHASE 9:
Report generation

PHASE 10:
Frontend

PHASE 11:
Sonar viewer

PHASE 12:
Map

PHASE 13:
Statistics

PHASE 14:
Demo mode

PHASE 15:
Testing

PHASE 16:
Integration

PHASE 17:
UI polish

PHASE 18:
Documentation

After every phase:

1. Inspect generated code.
2. Run relevant tests.
3. Run type/import checks.
4. Fix errors.
5. Continue.

Do not leave TODO placeholders for core functionality.

============================================================
36. IMPORTANT COPILOT BEHAVIOR
============================================================

Before modifying a file:

- inspect the existing file
- understand its purpose
- preserve working code

Do not rewrite the entire repository for small changes.

Do not create duplicate implementations.

Do not create multiple competing API clients.

Do not create multiple database systems.

Do not create multiple frontend frameworks.

Do not add dependencies without a reason.

Prefer simple maintainable code.

============================================================
37. FINAL ACCEPTANCE TEST
============================================================

The project is considered complete only when this workflow works:

START BACKEND

uvicorn backend.main:app --reload

START FRONTEND

npm run dev

OPEN DASHBOARD

↓

Upload sonar image

↓

Upload or select metadata

↓

Click Analyze

↓

Backend processes image

↓

Detector runs if model exists

OR

Demo Mode runs if explicitly selected

↓

Results appear

↓

Bounding boxes appear

↓

Detection table appears

↓

Statistics update

↓

Map markers appear

↓

Click marker

↓

Corresponding detection becomes selected

↓

Download CSV

↓

Download JSON

↓

No console errors

↓

No backend exceptions

============================================================
38. FINAL COMMANDS
============================================================

At the end, make sure these work:

Backend:

python -m pytest

Frontend:

npm run build

Frontend:

npm run dev

Backend:

uvicorn backend.main:app --reload

============================================================
39. FINAL RESPONSE FROM YOU
============================================================

After implementation, report:

1. Files created
2. Dependencies installed
3. Commands to start backend
4. Commands to start frontend
5. Test results
6. Build results
7. Whether AI model exists
8. Whether Demo Mode works
9. Dataset requirements
10. Remaining limitations

Do not say "complete" unless the acceptance test has been executed successfully.

Begin by inspecting the repository and then implement the project.