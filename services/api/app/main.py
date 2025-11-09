from fastapi import FastAPI
from sqlmodel import SQLModel, create_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://anip:anip_pw@postgres:5432/anip")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="ANIP API")

@app.on_event("startup")
def on_startup():
    # Keep empty for now (we'll add models later)
    with engine.connect() as conn:
        conn.exec_driver_sql("SELECT 1;")

@app.get("/health")
def health():
    return {"status": "ok"}
