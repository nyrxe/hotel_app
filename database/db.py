from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# SQLite database path (make sure it's in the root folder)
SQLALCHEMY_DATABASE_URL = "sqlite:///hotel_reviews.db"

# Create database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
