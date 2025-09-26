from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Use the MySQL connection URI from config (pymysql)
engine = create_engine(settings.mysql_uri, echo=True)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Dependency function to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
