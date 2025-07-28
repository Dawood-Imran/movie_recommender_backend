# Standard library imports
import os
from datetime import datetime, timedelta
from typing import List, Dict

# Third-party imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import firebase_admin
from firebase_admin import credentials, firestore, db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
CACHE_DURATION = 86400  # 1 day in seconds

# Firebase Configuration
FIREBASE_DB_URL = 'https://movie-recommender-f0ad3-default-rtdb.firebaseio.com'

# Validate environment variables
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY not found in environment variables. Make sure it's set in your .env file.")

# Initialize FastAPI app
app = FastAPI(
    title="Movie Recommender API",
    description="Backend API for the Movie Recommender application",
    version="1.0.0"
)

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase
def init_firebase():
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
        # Test connection
        ref = db.reference('/')
        data = ref.get()
        print(f"Successfully connected to Firebase RTDB!")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        raise

# TMDB API Functions
def fetch_trending_movies() -> List[Dict]:
    """
    Fetch trending movies from TMDB API
    """
    url = f"{TMDB_BASE_URL}/trending/movie/week"
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching TMDB data: {str(e)}")

async def get_cached_trending_movies() -> List[Dict]:
    """
    Get trending movies with caching
    """
    cache_ref = db.reference("cache/trending_movies")
    # Fetch cache document
    cache_doc = cache_ref.get()

    if cache_doc:
        cached_time = cache_doc.get("timestamp")
        if cached_time:
            # Convert string timestamp back to datetime for comparison
            cached_datetime = datetime.fromisoformat(cached_time)
            if (datetime.now() - cached_datetime).total_seconds() < CACHE_DURATION:
                return cache_doc.get("movies", [])

    movies = fetch_trending_movies()
    cache_ref.set({
        "movies": movies,
        "timestamp": datetime.now().isoformat()  # Convert datetime to ISO format string
    })
    return movies

# API Routes
@app.get("/")
def read_root():
    """
    Root endpoint
    """
    return {"status": "active", "message": "Movie Recommender API is running"}

@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/trending-movies", response_model=List[Dict])
async def get_trending_movies():
    """
    Get trending movies endpoint
    """
    return await get_cached_trending_movies()




# Initialize Firebase on startup
init_firebase()
     

 

