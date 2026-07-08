import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DATABASE_URL puede apuntar a SQLite (desarrollo) o PostgreSQL (producción).
# Ejemplo PostgreSQL: postgresql+psycopg2://user:pass@host/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sysiphus.db")

# connect_args={"check_same_thread": False} sólo es necesario para SQLite.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
