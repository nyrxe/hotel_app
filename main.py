from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database.db import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import joblib
from typing import Optional
import numpy as np

# Load the sentiment analysis model at startup
try:
    model = joblib.load("sentiment_pipeline_svc_20250601_1833.pkl")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

app = FastAPI()

# CORS (Cross-Origin Resource Sharing) — allows frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now; later you can restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add this Pydantic model class after the imports
class HotelReview(BaseModel):
    hotel_name: str
    positive_review: str
    negative_review: str
    reviewer_score: float
    sentiment_prediction: Optional[str] = None

class ReviewText(BaseModel):
    text: str

class TextInput(BaseModel):
    text: str

class SplitReviewResponse(BaseModel):
    positive: str
    negative: str

# API routes
@app.get("/api")
def root():
    return {"message": "Hotel Review API is up!"}

@app.get("/api/hotels")
def get_hotels(db: Session = Depends(get_db)):
    query = "SELECT DISTINCT Hotel_Name FROM reviews ORDER BY Hotel_Name"
    result = db.execute(sqlalchemy.text(query)).fetchall()
    return [row[0] for row in result]

@app.get("/api/reviews")
def get_reviews(hotel: str = None, db: Session = Depends(get_db)):
    if hotel:
        query = """
        SELECT Hotel_Name, Reviewer_Score, Positive_Review, Negative_Review 
        FROM reviews 
        WHERE Hotel_Name = :hotel
        ORDER BY Reviewer_Score DESC 
        LIMIT 10
        """
        result = db.execute(sqlalchemy.text(query), {"hotel": hotel}).fetchall()
    else:
        query = """
        SELECT Hotel_Name, Reviewer_Score, Positive_Review, Negative_Review 
        FROM reviews 
        ORDER BY Reviewer_Score DESC 
        LIMIT 10
        """
        result = db.execute(sqlalchemy.text(query)).fetchall()
    
    # Convert row objects to dictionaries with native Python types
    reviews = []
    for row in result:
        review_dict = dict(row._mapping)
        # Convert any numeric types to native Python types
        review_dict['Reviewer_Score'] = float(review_dict['Reviewer_Score'])
        reviews.append(review_dict)
    
    return reviews

@app.post("/api/reviews")
def create_review(review: HotelReview, db: Session = Depends(get_db)):
    if model:
        try:
            sentiment = model.predict([review.positive_review])[0]
            # Convert numpy type to string
            review.sentiment_prediction = str(sentiment)
        except Exception as e:
            print(f"Sentiment prediction error: {e}")
            review.sentiment_prediction = None
    
    query = """
    INSERT INTO reviews (Hotel_Name, Positive_Review, Negative_Review, Reviewer_Score, Sentiment_Prediction)
    VALUES (:hotel_name, :positive_review, :negative_review, :reviewer_score, :sentiment_prediction)
    """
    
    try:
        db.execute(
            sqlalchemy.text(query),
            {
                "hotel_name": review.hotel_name,
                "positive_review": review.positive_review,
                "negative_review": review.negative_review,
                "reviewer_score": float(review.reviewer_score),  # Convert to native float
                "sentiment_prediction": review.sentiment_prediction
            }
        )
        db.commit()
        return {
            "message": "Review added successfully",
            "sentiment": review.sentiment_prediction
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to add review: {str(e)}"}

@app.post("/predict")
def predict(input_data: TextInput):
    if not model:
        return {"error": "Model not loaded"}
    try:
        prediction = model.predict([input_data.text])[0]
        # Convert numpy type to string
        prediction = str(prediction)
        return {"prediction": prediction}
    except Exception as e:
        return {"error": f"Prediction failed: {str(e)}"}

@app.post("/split-review")
def split_review(review: TextInput):
    if not model:
        return {"error": "Model not loaded"}
    
    # Split text into sentences (simple split by period)
    sentences = [s.strip() + "." for s in review.text.split(".") if s.strip()]
    
    try:
        # Predict sentiment for each sentence
        predictions = model.predict(sentences)
        # Convert numpy array to list of strings and print for debugging
        predictions = [str(pred).lower().strip() for pred in predictions]
        print(f"Predictions for sentences: {list(zip(sentences, predictions))}")
        
        # Separate positive and negative sentences
        positive_sentences = [sent for sent, pred in zip(sentences, predictions) if "pos" in pred.lower()]
        negative_sentences = [sent for sent, pred in zip(sentences, predictions) if "neg" in pred.lower()]
        
        print(f"Positive sentences: {positive_sentences}")
        print(f"Negative sentences: {negative_sentences}")
        
        # Join sentences or provide default text if empty
        positive_text = " ".join(positive_sentences) if positive_sentences else "No positive aspects mentioned."
        negative_text = " ".join(negative_sentences) if negative_sentences else "No negative aspects mentioned."
        
        response = {
            "positive": positive_text,
            "negative": negative_text
        }
        print(f"Returning response: {response}")
        return response
    except Exception as e:
        print(f"Error in split_review: {str(e)}")
        return {"error": f"Failed to split review: {str(e)}"}

# Mount static files AFTER defining API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")

