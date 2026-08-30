import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from sqlalchemy.orm import Session
from backend.ai.yolo_detector import ModelUnavailableError, YoloDetector
from backend.database.database import get_db
from backend.database.repository import AnomalyRepository
from backend.reports.generator import csv_report, json_report
from backend.schemas.metadata import Metadata
from backend.services.analysis_service import analyze, DATA_DIR

router = APIRouter(prefix="/api")


def parse_metadata(value: str | None) -> Metadata:
    if not value: return Metadata()
    try: return Metadata.model_validate(json.loads(value))
    except Exception as exc: raise HTTPException(422, "Invalid metadata JSON or coordinates") from exc


@router.post("/analyze")
async def analyze_upload(file: UploadFile = File(...), metadata: str | None = Form(None), db: Session = Depends(get_db)):
    if not file.filename: raise HTTPException(400, "Missing image filename")
    try: return analyze(await file.read(), file.filename, parse_metadata(metadata), AnomalyRepository(db))
    except ModelUnavailableError as exc:
        raise HTTPException(503, {"code": exc.code, "message": exc.message}) from exc
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc


@router.post("/demo/run")
async def demo_upload(file: UploadFile = File(...), metadata: str | None = Form(None), db: Session = Depends(get_db)):
    try: return analyze(await file.read(), file.filename or "demo.png", parse_metadata(metadata), AnomalyRepository(db), demo=True)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc


@router.get("/demo/status")
def demo_status(): return {"available": True, "label": "DEMO / SAMPLE DATA", "model_available": YoloDetector().available}


@router.get("/detections")
def detections(survey_id: str | None = None, db: Session = Depends(get_db)): return [json_report([item])[0] for item in AnomalyRepository(db).list(survey_id)]


@router.get("/detections/{anomaly_id}")
def detection(anomaly_id: int, db: Session = Depends(get_db)):
    item = AnomalyRepository(db).get(anomaly_id)
    if not item: raise HTTPException(404, "Detection not found")
    return json_report([item])[0]


@router.delete("/detections/{anomaly_id}")
def delete_detection(anomaly_id: int, db: Session = Depends(get_db)):
    if not AnomalyRepository(db).delete(anomaly_id): raise HTTPException(404, "Detection not found")
    return {"deleted": True}


@router.get("/statistics")
def statistics(db: Session = Depends(get_db)): return AnomalyRepository(db).statistics()


@router.get("/reports/{survey_id}/json")
def report_json(survey_id: str, db: Session = Depends(get_db)): return JSONResponse(json_report(AnomalyRepository(db).list(survey_id)))


@router.get("/reports/{survey_id}/csv")
def report_csv(survey_id: str, db: Session = Depends(get_db)): return PlainTextResponse(csv_report(AnomalyRepository(db).list(survey_id)), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{survey_id}.csv"'})


@router.get("/images/{analysis_id}")
def annotated_image(analysis_id: str):
    path = DATA_DIR / "processed" / f"{analysis_id}.png"
    if not path.exists(): raise HTTPException(404, "Annotated image not found")
    return Response(path.read_bytes(), media_type="image/png")
