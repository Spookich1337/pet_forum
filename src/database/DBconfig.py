from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DBmodels import *


DATABASE_URL = "postgresql://admin:admin@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()