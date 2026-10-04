from app.db.connection import engine
from app.db.models import Base

Base.metadata.create_all(bind=engine)

print("Database tables created succesfully.")