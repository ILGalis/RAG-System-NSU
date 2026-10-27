from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import spaces
from app.core.error import register_error_handlers
from backend.db.connection import engine

app = FastAPI(
    title="NSU RAG API",
    version="0.1.0",
)

register_error_handlers(app)

app.include_router(spaces.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}