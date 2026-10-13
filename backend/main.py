
from fastapi import FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.connection import engine
from app.models import RagSpace
from app.schemas import RagSpaceCreate, RagSpaceResponse, RagSpaceUpdate

app = FastAPI(
    title="NSU RAG API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

