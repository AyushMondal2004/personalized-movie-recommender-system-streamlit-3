import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Collections
user_col = db['user']
history_col = db['history']
otp_col = db['otp']

from datetime import datetime

def log_search_history(user_id, query=None, genres=None, year=None, movie_id=None):
    history_col.insert_one({
        "user_id": user_id,
        "query": query,
        "genres": genres,
        "year": year,
        "movie_id": movie_id,
        "timestamp": datetime.utcnow()
    })
