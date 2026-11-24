from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes import auth, document, invitations, members, spaces
from app.core.error import register_error_handlers
from backend.db.connection import engine

app = FastAPI(
    title="NSU RAG API",
    version="0.1.1",
)

register_error_handlers(app)

app.include_router(spaces.router)
app.include_router(auth.router)
app.include_router(document.router)
app.include_router(members.router)
app.include_router(invitations.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/db")
def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}