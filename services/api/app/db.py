from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://anip:anip_pw@postgres:5432/anip"
)

engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Create all tables if not exist."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provide a session context for routes or scripts."""
    with Session(engine) as session:
        yield session
