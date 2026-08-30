from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./marine_debris.db"
    model_path: str = "backend/models/best.pt"
    confidence_threshold: float = 0.70
    max_upload_size_mb: int = 20
    supported_classes: dict[int, str] = {
        0: "ghost_net", 1: "shipwreck", 2: "pipe", 3: "cylinder", 4: "debris"
    }
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def model_file(self) -> Path:
        return Path(self.model_path) if Path(self.model_path).is_absolute() else BASE_DIR.parent / self.model_path


settings = Settings()
