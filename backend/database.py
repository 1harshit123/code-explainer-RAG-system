import os
from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel, create_engine, Session, text
from dotenv import load_dotenv
from .model import *

# Locate and load the root .env file configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../.env"))
load_dotenv(dotenv_path=ENV_FILE_PATH)

# Fetch database credentials safely
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "coderag")

# Format the PostgreSQL connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Initialising of the tables"""
    try:
        SQLModel.metadata.create_all(engine)
        print("Engine is running successfully and created the tables in the database")
    except Exception as e:
        print("Error: In creating in running the engine", {e})


