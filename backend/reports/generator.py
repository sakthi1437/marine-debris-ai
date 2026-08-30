import csv
import io
from backend.database.models import Anomaly

FIELDS = ["ID", "Survey ID", "Image", "Object Type", "Model Confidence", "Final Confidence", "Priority", "Latitude", "Longitude", "X1", "Y1", "X2", "Y2", "Width", "Height", "Metadata Source", "Created At"]


def row(item: Anomaly) -> dict:
    return {"ID": item.id, "Survey ID": item.survey_id, "Image": item.image_name, "Object Type": item.object_type, "Model Confidence": item.model_confidence, "Final Confidence": item.final_confidence, "Priority": item.priority, "Latitude": item.latitude, "Longitude": item.longitude, "X1": item.x1, "Y1": item.y1, "X2": item.x2, "Y2": item.y2, "Width": item.width, "Height": item.height, "Metadata Source": item.metadata_source, "Created At": item.created_at.isoformat()}


def csv_report(items: list[Anomaly]) -> str:
    output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=FIELDS); writer.writeheader(); writer.writerows(row(item) for item in items); return output.getvalue()


def json_report(items: list[Anomaly]) -> list[dict]: return [row(item) for item in items]
