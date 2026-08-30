import csv
import json
from pathlib import Path
from backend.location.base_location import Location, LocationProvider


class MetadataLocationProvider(LocationProvider):
    source = "metadata"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def get_location(self) -> Location:
        try:
            if self.path.suffix.lower() == ".json":
                values = json.loads(self.path.read_text(encoding="utf-8"))
            elif self.path.suffix.lower() == ".csv":
                with self.path.open(newline="", encoding="utf-8") as stream:
                    values = next(csv.DictReader(stream))
            else:
                raise ValueError("Metadata must be a JSON or CSV file")
            return Location(float(values["latitude"]), float(values["longitude"]), self.source)
        except (OSError, KeyError, StopIteration, TypeError, ValueError) as exc:
            raise ValueError("Metadata file must contain valid latitude and longitude") from exc
