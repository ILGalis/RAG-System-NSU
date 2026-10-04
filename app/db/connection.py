import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER","nsu_rag"),
    password=os.getenv("POSTGRES_PASSWORD", "local_dev_password"),
    host=os.getenv("POSTGRES_HOST","localhost"),
    port=int(os.getenv("POSTGRES_PORT","5432")),
    database=os.getenv("POSTGRES_DB","nsu_rag"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def check_connection()->bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True