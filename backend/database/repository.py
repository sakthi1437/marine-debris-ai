from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.database.models import Anomaly


class AnomalyRepository:
    def __init__(self, db: Session): self.db = db

    def create(self, values: dict) -> Anomaly:
        item = Anomaly(**values); self.db.add(item); self.db.commit(); self.db.refresh(item); return item

    def get(self, anomaly_id: int): return self.db.get(Anomaly, anomaly_id)
    def list(self, survey_id: str | None = None):
        query = self.db.query(Anomaly)
        return query.filter(Anomaly.survey_id == survey_id).all() if survey_id else query.order_by(Anomaly.created_at.desc()).all()
    def delete(self, anomaly_id: int) -> bool:
        item = self.get(anomaly_id)
        if not item: return False
        self.db.delete(item); self.db.commit(); return True
    def delete_by_survey(self, survey_id: str) -> int:
        count = self.db.query(Anomaly).filter(Anomaly.survey_id == survey_id).delete(); self.db.commit(); return count
    def count(self) -> int: return self.db.query(func.count(Anomaly.id)).scalar() or 0
    def statistics(self) -> dict:
        rows = self.list()
        result = {"total": len(rows), "high": 0, "medium": 0, "low": 0, "by_type": {}}
        for row in rows:
            result[row.priority.lower()] += 1
            result["by_type"][row.object_type] = result["by_type"].get(row.object_type, 0) + 1
        return result
