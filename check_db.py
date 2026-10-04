from app.db.connection import check_connection

if check_connection():
    print("PostgreSQL connection: OK")