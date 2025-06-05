import pandas as pd
from sqlalchemy import create_engine

# Load the CSV file
csv_path = "Hotel_Reviews.csv"  # Make sure this file is in the same folder
df = pd.read_csv(csv_path)

# Keep only the columns we need
df = df[["Hotel_Name", "Reviewer_Score", "Positive_Review", "Negative_Review"]]

# Optional: remove rows with no reviews
df = df[(df["Positive_Review"].notnull()) & (df["Negative_Review"].notnull())]

# Create SQLite engine
engine = create_engine("sqlite:///hotel_reviews.db")

# Save DataFrame to SQLite database
df.to_sql("reviews", con=engine, if_exists="replace", index=False)

print("✅ Hotel reviews successfully loaded into hotel_reviews.db")
