# Personalized Movie Recommender System

A hybrid movie recommender system using Streamlit (frontend), Python (backend), MongoDB Atlas, and TMDb API.

## Features
- User authentication (register, login, OTP-based password reset)
- Real-time movie data from TMDb
- Hybrid recommendations (content-based + collaborative filtering)
- User history tracking

## Tech Stack
- **Frontend:** Streamlit
- **Backend:** Python
- **Database:** MongoDB Atlas
- **Movie Data:** TMDb API

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` with your API keys and MongoDB URI (see `.env.example`).
3. Run the app: `streamlit run frontend/app.py`

---

## Directory Structure
```
personalized_movie_recommender_system/
│   README.md
│   requirements.txt
│   .env.example
│
├── backend/
│   ├── db.py           # MongoDB connection
│   ├── tmdb.py         # TMDb API wrapper
│   ├── auth.py         # Authentication logic
│   ├── recommender.py  # Recommendation engine
│   └── utils.py        # Utility functions
│
├── frontend/
│   └── app.py          # Streamlit main app
│
└── config.py           # Central config (API keys, etc.)
```
