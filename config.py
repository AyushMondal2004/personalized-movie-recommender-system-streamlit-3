import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
