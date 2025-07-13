import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'


def search_movies(query):
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {'api_key': TMDB_API_KEY, 'query': query}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json().get('results', []), None
    except requests.RequestException as e:
        error_msg = f"TMDb API error (search_movies): {e}"
        print(error_msg)
        return [], error_msg


def get_trending_movies():
    url = f"{TMDB_BASE_URL}/trending/movie/week"
    params = {'api_key': TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json().get('results', []), None
    except requests.RequestException as e:
        error_msg = f"TMDb API error (get_trending_movies): {e}"
        print(error_msg)
        return [], error_msg


def get_movie_details(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {'api_key': TMDB_API_KEY, 'append_to_response': 'credits,keywords'}
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"TMDb API error (get_movie_details): {e}")
        return {}


def discover_movies(genres=None, year=None):
    url = f"{TMDB_BASE_URL}/discover/movie"
    params = {'api_key': TMDB_API_KEY, 'sort_by': 'popularity.desc'}
    if genres:
        params['with_genres'] = ','.join(str(g) for g in genres)
    if year:
        params['primary_release_year'] = year
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json().get('results', []), None
    except requests.RequestException as e:
        error_msg = f"TMDb API error (discover_movies): {e}"
        print(error_msg)
        return [], error_msg

