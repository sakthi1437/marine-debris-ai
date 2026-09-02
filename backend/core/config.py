from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = ""
    model_path: str = "backend/models/best.pt"
    confidence_threshold: float = 0.70
    max_upload_size_mb: int = 20
    supported_classes: dict[int, str] = {
        0: "Airplane", 1: "Drowning Victim", 2: "Mine", 3: "Shipwreck"
    }
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def model_file(self) -> Path:
        path = Path(self.model_path)
        return path.resolve() if path.is_absolute() else (PROJECT_DIR / path).resolve()

    @property
    def database_path(self) -> Path:
        return (PROJECT_DIR / "marine_debris.db").resolve()

    def __init__(self, **data):
        super().__init__(**data)
        if not self.database_url:
            self.database_url = f"sqlite:///{self.database_path}"


settings = Settings()
