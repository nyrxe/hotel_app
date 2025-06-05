from sqlalchemy import create_engine, text

# Create database engine
engine = create_engine("sqlite:///hotel_reviews.db", connect_args={"check_same_thread": False})

def update_schema():
    with engine.connect() as conn:
        try:
            # Add the Sentiment_Prediction column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE reviews 
                ADD COLUMN Sentiment_Prediction TEXT
            """))
            conn.commit()
            print("✅ Successfully added Sentiment_Prediction column")
        except Exception as e:
            print(f"Note: {str(e)}")
            # If error occurs (e.g., column already exists), just continue
            pass

if __name__ == "__main__":
    update_schema() 