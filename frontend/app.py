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
    selected_genres = st.sidebar.multiselect("Genres", list(genre_options.keys()))
    year_range = st.sidebar.slider("Release Year", 1950, 2025, (2000, 2025))
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
    if filter_clicked and (selected_genres or year_range):
        genre_ids = [genre_options[g] for g in selected_genres]
        # If full range is selected, ignore year filter
        year = None if year_range == (1950, 2025) else year_range[0]
        with st.spinner("Searching with filters..."):
            results, api_error = tmdb.discover_movies(genres=genre_ids, year=year, num_movies=50)
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
        # Genre ID to name mapping (should match TMDb)
        genre_id_to_name = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"}
        num_cols = 4
        movies_to_show = results[:50]
        for i in range(0, len(movies_to_show), num_cols):
            cols = st.columns(num_cols)
            for j, movie in enumerate(movies_to_show[i:i+num_cols]):
                with cols[j]:
                    st.image(f"https://image.tmdb.org/t/p/w200{movie.get('poster_path')}", width=150)
                    # Movie title as clickable link to details page
                    if st.button(f"{movie.get('title', 'No Title')} ({movie.get('release_date', '')[:4]})", key=f"title_{movie.get('id')}"):
                        st.session_state['page'] = 'movie_detail'
                        st.session_state['selected_movie_id'] = movie.get('id')
                    genre_names = [genre_id_to_name.get(g, str(g)) for g in movie.get('genre_ids', [])]
                    st.write(f"Genres: {', '.join(genre_names)}")
                    st.write(f"Rating: {movie.get('vote_average', 0)}/10")
                    # Show main two cast members if available
                    details = tmdb.get_movie_details(movie.get('id'))
                    cast = details.get('credits', {}).get('cast', [])
                    if cast:
                        main_cast = ', '.join([c['name'] for c in cast[:2]])
                        st.write(f"Main Cast: {main_cast}")

elif st.session_state['page'] == 'movie_detail':
    # Movie detail view
    movie_id = st.session_state.get('selected_movie_id')
    if movie_id is not None:
        details = tmdb.get_movie_details(movie_id)
        # Back button at top left
        if st.button('← Back', key='back_button'):
            st.session_state['page'] = 'main'
            st.session_state.pop('selected_movie_id', None)
            st.rerun()
        # Show poster and all details
        col_img, col_info = st.columns([1,2])
        with col_img:
            st.image(f"https://image.tmdb.org/t/p/w500{details.get('poster_path')}", width=250)
        with col_info:
            st.markdown(f"# {details.get('title', 'No Title')}")
            st.write(f"**Tagline:** {details.get('tagline', '')}")
            st.write(f"**Overview:** {details.get('overview', '')}")
            st.write(f"**Release Date:** {details.get('release_date', 'N/A')}")
            st.write(f"**Runtime:** {details.get('runtime', 'N/A')} min")
            st.write(f"**Status:** {details.get('status', 'N/A')}")
            st.write(f"**Budget:** ${details.get('budget', 0):,}")
            st.write(f"**Revenue:** ${details.get('revenue', 0):,}")
            st.write(f"**Popularity:** {details.get('popularity', 'N/A')}")
            st.write(f"**Vote Average:** {details.get('vote_average', 'N/A')}")
            st.write(f"**Vote Count:** {details.get('vote_count', 'N/A')}")
            st.write(f"**Homepage:** {details.get('homepage', 'N/A')}")
            st.write(f"**Original Title:** {details.get('original_title', 'N/A')}")
            st.write(f"**Original Language:** {details.get('original_language', 'N/A')}")
            st.write(f"**Movie ID:** {details.get('id', 'N/A')}")
            # Genres
            genres = details.get('genres', [])
            if genres:
                st.write(f"**Genres:** {', '.join([g['name'] for g in genres])}")
            # Keywords
            keywords = details.get('keywords', {}).get('keywords', [])
            if keywords:
                st.write(f"**Keywords:** {', '.join([k['name'] for k in keywords])}")
            # Production companies
            prod_comp = details.get('production_companies', [])
            if prod_comp:
                st.write(f"**Production Companies:** {', '.join([c['name'] for c in prod_comp])}")
            # Production countries
            prod_countries = details.get('production_countries', [])
            if prod_countries:
                st.write(f"**Production Countries:** {', '.join([c['name'] for c in prod_countries])}")
            # Spoken languages
            spoken_langs = details.get('spoken_languages', [])
            if spoken_langs:
                st.write(f"**Spoken Languages:** {', '.join([l['name'] for l in spoken_langs])}")
            # Cast
            credits = details.get('credits', {})
            cast = credits.get('cast', [])
            if cast:
                st.write(f"**Cast:** {', '.join([c['name'] for c in cast[:10]])}")
            # Crew
            crew = credits.get('crew', [])
            if crew:
                st.write(f"**Crew:** {', '.join([c['name']+' ('+c['job']+')' for c in crew[:10]])}")

    st.sidebar.header("Advanced Filters")
    genre_options = {
        "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402, "Mystery": 9648, "Romance": 10749, "Science Fiction": 878, "TV Movie": 10770, "Thriller": 53, "War": 10752, "Western": 37
    }
    selected_genres = st.sidebar.multiselect("Genres", list(genre_options.keys()))
    year_range = st.sidebar.slider("Release Year", 1950, 2025, (2000, 2025))
    filter_clicked = st.sidebar.button("Apply Filters")

    
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
    if filter_clicked and (selected_genres or year_range):
        genre_ids = [genre_options[g] for g in selected_genres]
        # If full range is selected, ignore year filter
        year = None if year_range == (1950, 2025) else year_range[0]
        with st.spinner("Searching with filters..."):
            results, api_error = tmdb.discover_movies(genres=genre_ids, year=year, num_movies=50)
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
        # Genre ID to name mapping (should match TMDb)
        genre_id_to_name = {28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance", 878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"}
        num_cols = 4
        movies_to_show = results[:50]
        for i in range(0, len(movies_to_show), num_cols):
            cols = st.columns(num_cols)
            for j, movie in enumerate(movies_to_show[i:i+num_cols]):
                with cols[j]:
                    st.image(f"https://image.tmdb.org/t/p/w200{movie.get('poster_path')}", width=150)
                    # Movie title as clickable link to details page
                    if st.button(f"{movie.get('title', 'No Title')} ({movie.get('release_date', '')[:4]})", key=f"title_{movie.get('id')}"):
                        st.session_state['page'] = 'movie_detail'
                        st.session_state['selected_movie_id'] = movie.get('id')
                    # Optionally, display as hyperlink style
                    # st.markdown(f"<a href='#' style='color:#E50914;font-weight:bold;'>{movie.get('title', 'No Title')} ({movie.get('release_date', '')[:4]})</a>", unsafe_allow_html=True)
                    genre_names = [genre_id_to_name.get(g, str(g)) for g in movie.get('genre_ids', [])]
                    st.write(f"Genres: {', '.join(genre_names)}")
                    st.write(f"Rating: {movie.get('vote_average', 0)}/10")
                    # Show main two cast members if available
                    details = tmdb.get_movie_details(movie.get('id'))
                    cast = details.get('credits', {}).get('cast', [])
                    if cast:
                        main_cast = ', '.join([c['name'] for c in cast[:2]])
                        st.write(f"Main Cast: {main_cast}")
