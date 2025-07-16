import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend import auth, tmdb, recommender
from backend.tmdb import discover_movies
from backend.db import log_search_history

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# Page 1: Authentication
if st.session_state['page'] == 'login':
    st.title("Login")
    st.info("Please enter your username and password to login.")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        success, user = auth.login_user(username, password)
        if success:
            st.session_state['user'] = user
            st.session_state['page'] = 'main'
            st.success("Login successful! Welcome back.")
            st.rerun()
        else:
            st.error(user)
    if st.button("Go to Register"):
        st.session_state['page'] = 'register'
        st.rerun()

elif st.session_state['page'] == 'register':
    st.title("Register")
    st.info("Create a new account. All fields are required except favorite genres.")
    with st.form("register_form"):
        username = st.text_input("Username")
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        address = st.text_input("Address")
        password = st.text_input("Password", type="password")
        dob = st.date_input("Date of Birth")
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        genre_options = [
            "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction", "TV Movie", "Thriller", "War", "Western"
        ]
        genres = st.multiselect("Favorite Genres (optional)", genre_options)
        submitted = st.form_submit_button("Register")
        if submitted:
            user_data = {
                'username': username,
                'name': name,
                'phone': phone,
                'email': email,
                'address': address,
                'password': password,
                'dob': str(dob),
                'gender': gender,
                'genres': genres
            }
            success, msg = auth.register_user(user_data)
            if success:
                st.success(msg + " Please login.")
                st.session_state['page'] = 'login'
                st.rerun()
            else:
                st.error(msg)
    if st.button("Go to Login"):
        st.session_state['page'] = 'login'
        st.rerun()



elif st.session_state['page'] == 'main':
    # Top-right logout button
    col2 = st.columns([1])[0]
    with col2:
        if st.button("Logout"):
            st.session_state.clear()
            st.session_state['page'] = 'login'
            st.rerun()

    # Sidebar filters
    st.sidebar.header("Advanced Filters")
    genre_options = {
        "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402, "Mystery": 9648, "Romance": 10749, "Science Fiction": 878, "TV Movie": 10770, "Thriller": 53, "War": 10752, "Western": 37
    }
    selected_genres = st.sidebar.multiselect("Genres", list(genre_options.keys()), key="sidebar_genres_main")
    year_range = st.sidebar.slider("Release Year", 1950, 2025, (2000, 2025))
    vote_average_range = st.sidebar.slider("Rating", 0.0, 10.0, (0.0, 10.0), step=0.1)
    language_options = [
        ("Any", ""), ("English", "en"), ("Hindi", "hi"), ("French", "fr"), ("Spanish", "es"), ("German", "de"), ("Japanese", "ja"), ("Korean", "ko"), ("Chinese", "zh"), ("Italian", "it"), ("Russian", "ru")
    ]
    selected_language = st.sidebar.selectbox("Language", [x[0] for x in language_options], index=0)
    region_options = [
        ("Any", ""), ("United States", "US"), ("India", "IN"), ("France", "FR"), ("Spain", "ES"), ("Germany", "DE"), ("Japan", "JP"), ("Korea", "KR"), ("China", "CN"), ("Italy", "IT"), ("Russia", "RU")
    ]
    selected_region = st.sidebar.selectbox("Region", [x[0] for x in region_options], index=0)
    # Safe mapping for codes
    language_map = dict(language_options)
    region_map = dict(region_options)
    language_code = language_map.get(selected_language, None)
    region_code = region_map.get(selected_region, None)
    filter_clicked = st.sidebar.button("Apply Filters")

    # Main UI (welcome, search, grid, etc.)
    st.title("CineMatch: Your Personal Movie Companion")
    user = st.session_state.get('user', {})
    user_name = user.get('name') or user.get('username', 'User')
    st.markdown(f"### Welcome, {user_name}!")
    st.subheader("Search for Movies")
    with st.form("search_form"):
        query = st.text_input("Movie Title")
        search_clicked = st.form_submit_button("Search")
    results, api_error = [], None
    # Priority: Filters > Title Search > Trending
    user_id = user.get('_id') or user.get('username')
    if filter_clicked and (selected_genres or year_range or selected_language or selected_region):
        genre_ids = [genre_options[g] for g in selected_genres]
        # If full range is selected, ignore year filter
        year = None if year_range == (1950, 2025) else year_range[0]
        # Get language/region code
        language_code = dict(language_options)[selected_language]
        region_code = dict(region_options)[selected_region]
        with st.spinner("Searching with filters..."):
            results, api_error = tmdb.discover_movies(genres=genre_ids, year=year, num_movies=50, language=language_code or None, region=region_code or None)
        # Log filter search
        log_search_history(user_id, query=None, genres=selected_genres, year=year)
    elif query and search_clicked:
        with st.spinner("Searching for movies..."):
            results, api_error = tmdb.search_movies(query, num_movies=50)
        # Log title search
        log_search_history(user_id, query=query, genres=None, year=None)
    elif not query and not filter_clicked:
        with st.spinner("Loading trending movies..."):
            results, api_error = tmdb.get_trending_movies(num_movies=50)
    if api_error:
        st.error(f"Movie search failed: {api_error}")
    elif ((query and search_clicked) or filter_clicked) and not results:
        st.warning("No movies found for your search.")
    elif results:
        # Only apply vote average filter if Advanced Filters are used
        if filter_clicked:
            results = [m for m in results if vote_average_range[0] <= m.get('vote_average', 0) <= vote_average_range[1]]
        # Sort results by vote_count in descending order
        results = sorted(results, key=lambda m: m.get('vote_count', 0), reverse=True)
        # Genre ID to name mapping (should match TMDb)
        genre_id_to_name = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"}
        num_cols = 4
        movies_to_show = results[:50]
        for i in range(0, len(movies_to_show), num_cols):
            cols = st.columns(num_cols)
            for j, movie in enumerate(movies_to_show[i:i+num_cols]):
                with cols[j]:
                    st.image(f"https://image.tmdb.org/t/p/w200{movie.get('poster_path')}", width=150)
                    # Prepare movie info for HTML
                    genre_names = [genre_id_to_name.get(g, str(g)) for g in movie.get('genre_ids', [])]
                    details = tmdb.get_movie_details(movie.get('id'))
                    cast = details.get('credits', {}).get('cast', [])
                    main_cast = ', '.join([c['name'] for c in cast[:2]]) if cast else ''
                    movie_html = f'''
                    <div class="movie-card">
                        <div class="movie-title">{movie.get('title', 'No Title')} ({movie.get('release_date', '')[:4]})</div>
                        <div class="movie-info">Genres: {', '.join(genre_names)}</div>
                        <div class="movie-rating">Rating: {movie.get('vote_average', 0):.2f}/10</div>
                        <div class="movie-cast">Main Cast: {main_cast}</div>
                    </div>
                    '''
                    st.markdown(movie_html, unsafe_allow_html=True)

# Inject custom CSS for movie cards
with open(os.path.join(os.path.dirname(__file__), "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

