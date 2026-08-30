from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.core.logging_config import configure_logging
from backend.database.database import init_db

configure_logging()
init_db()
app = FastAPI(title="Underwater Marine Debris Intelligence", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health(): return {"status": "ok", "service": "marine-debris-ai"}
