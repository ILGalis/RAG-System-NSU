from fastapi import FastAPI
from sqlalchemy import text

from app.db.connection import engine

app = FastAPI(
    title="NSU RAG API",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.get("/health/db")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok","database": "postgresql"}