from fastapi import FastAPI 

app = FastAPI(title="NSU RAG API")

@app.get("/health")
def health_check():
    return {"status": "ok"}