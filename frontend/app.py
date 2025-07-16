import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from backend import auth, tmdb
from backend.db import log_search_history

st.set_page_config(page_title="Personalized Movie Recommender", layout="wide")

if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# ✅ Page 1: Authentication with Forgot Password + Resend OTP
if st.session_state['page'] == 'login':
    st.title("Login")
    st.info("Please enter your username or email and password to login.")

    identifier = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")

    # Init session states
    st.session_state.setdefault('forgot_pw_mode', False)
    st.session_state.setdefault('reset_pw_email', '')
    st.session_state.setdefault('reset_pw_otp_sent', False)

    if not st.session_state['forgot_pw_mode']:
        if st.button("Login"):
            success, user = auth.login_user(identifier, password)
            if success:
                st.session_state['user'] = user
                st.session_state['page'] = 'main'
                st.success("Login successful! Welcome back.")
                st.rerun()
            else:
                st.error(user)

        if st.button("Forgot Password?"):
            st.session_state['forgot_pw_mode'] = True
            st.rerun()

        if st.button("Go to Register"):
            st.session_state['page'] = 'register'
            st.rerun()

    else:
        st.subheader("Forgot Password")

        if not st.session_state['reset_pw_otp_sent']:
            email = st.text_input("Enter your registered email", value=st.session_state['reset_pw_email'])

            if st.button("Send OTP"):
                success, msg = auth.initiate_password_reset(email)
                st.session_state['reset_pw_email'] = email
                if success:
                    st.session_state['reset_pw_otp_sent'] = True
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

            if st.button("Back to Login"):
                st.session_state['forgot_pw_mode'] = False
                st.session_state['reset_pw_email'] = ''
                st.session_state['reset_pw_otp_sent'] = False
                st.rerun()
        else:
            st.write(f"OTP sent to: {st.session_state['reset_pw_email']}")
            otp = st.text_input("Enter OTP")
            new_password = st.text_input("New Password", type="password")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Reset Password"):
                    success, msg = auth.reset_password(st.session_state['reset_pw_email'], otp, new_password)
                    if success:
                        st.success("Password reset successful! Please login.")
                        st.session_state['forgot_pw_mode'] = False
                        st.session_state['reset_pw_email'] = ''
                        st.session_state['reset_pw_otp_sent'] = False
                        st.rerun()
                    else:
                        st.error(msg)

            with col2:
                if st.button("Resend OTP"):
                    success, msg = auth.initiate_password_reset(st.session_state['reset_pw_email'])
                    if success:
                        st.success("OTP resent successfully.")
                    else:
                        st.error(msg)

            if st.button("Back to Login"):
                st.session_state['forgot_pw_mode'] = False
                st.session_state['reset_pw_email'] = ''
                st.session_state['reset_pw_otp_sent'] = False
                st.rerun()

# ✅ Page 2: Registration
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
            "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family",
            "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction",
            "TV Movie", "Thriller", "War", "Western"
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

# ✅ Page 3: Main Movie Search with Filters
elif st.session_state['page'] == 'main':
    if st.button("Logout"):
        st.session_state.clear()
        st.session_state['page'] = 'login'
        st.rerun()

    # Sidebar Filters
    st.sidebar.header("Advanced Filters")
    genre_options = {
        "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35, "Crime": 80, "Documentary": 99,
        "Drama": 18, "Family": 10751, "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
        "Mystery": 9648, "Romance": 10749, "Science Fiction": 878, "TV Movie": 10770, "Thriller": 53,
        "War": 10752, "Western": 37
    }

    selected_genres = st.sidebar.multiselect("Genres", list(genre_options.keys()), key="sidebar_genres_main")
    year_range = st.sidebar.slider("Release Year", 1950, 2025, (2000, 2025), key="sidebar_year_main")
    vote_average_range = st.sidebar.slider("Rating", 0.0, 10.0, (0.0, 10.0), step=0.1, key="sidebar_rating_main")

    language_options = [
        ("Any", ""), ("English", "en"), ("Hindi", "hi"), ("French", "fr"), ("Spanish", "es"),
        ("German", "de"), ("Japanese", "ja"), ("Korean", "ko"), ("Chinese", "zh"),
        ("Italian", "it"), ("Russian", "ru")
    ]
    selected_language = st.sidebar.selectbox("Language", [x[0] for x in language_options], index=0, key="sidebar_language_main")

    region_options = [
        ("Any", ""), ("United States", "US"), ("India", "IN"), ("France", "FR"), ("Spain", "ES"),
        ("Germany", "DE"), ("Japan", "JP"), ("Korea", "KR"), ("China", "CN"),
        ("Italy", "IT"), ("Russia", "RU")
    ]
    selected_region = st.sidebar.selectbox("Region", [x[0] for x in region_options], index=0, key="sidebar_region_main")

    def clear_filter_session_state():
        keys_to_clear = [
            "sidebar_genres_main", "sidebar_year_main", "sidebar_rating_main",
            "sidebar_language_main", "sidebar_region_main"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.experimental_rerun()

    if st.sidebar.button("Clear Filters"):
        clear_filter_session_state()

    filter_clicked = st.sidebar.button("Apply Filters")

    # Main UI
    st.title("CineMatch: Your Personal Movie Companion")
    user = st.session_state.get('user', {})
    st.markdown(f"### Welcome, {user.get('name') or user.get('username', 'User')}!")

    with st.form("search_form"):
        query = st.text_input("Movie Title")
        search_clicked = st.form_submit_button("Search")

    results, api_error = [], None
    user_id = user.get('_id') or user.get('username')

    if filter_clicked and (selected_genres or year_range or selected_language or selected_region):
        genre_ids = [genre_options[g] for g in selected_genres]
        year = None if year_range == (1950, 2025) else year_range[0]
        language_code = dict(language_options)[selected_language]
        region_code = dict(region_options)[selected_region]
        with st.spinner("Searching with filters..."):
            results, api_error = tmdb.discover_movies(genres=genre_ids, year=year, num_movies=50,
                                                      language=language_code or None, region=region_code or None)
        log_search_history(user_id, query=None, genres=selected_genres, year=year)

    elif query and search_clicked:
        with st.spinner("Searching for movies..."):
            results, api_error = tmdb.search_movies(query, num_movies=50)
        log_search_history(user_id, query=query, genres=None, year=None)

    elif not query and not filter_clicked:
        with st.spinner("Loading trending movies..."):
            results, api_error = tmdb.get_trending_movies(num_movies=50)

    if api_error:
        st.error(f"Movie search failed: {api_error}")
    elif ((query and search_clicked) or filter_clicked) and not results:
        st.warning("No movies found for your search.")
    elif results:
        if filter_clicked:
            results = [m for m in results if vote_average_range[0] <= m.get('vote_average', 0) <= vote_average_range[1]]

        results = sorted(results, key=lambda m: m.get('vote_count', 0), reverse=True)

        genre_id_to_name = {v: k for k, v in genre_options.items()}
        num_cols = 4
        for i in range(0, len(results[:50]), num_cols):
            cols = st.columns(num_cols)
            for j, movie in enumerate(results[i:i+num_cols]):
                with cols[j]:
                    st.image(f"https://image.tmdb.org/t/p/w200{movie.get('poster_path')}", width=150)
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

# ✅ Inject Custom CSS
with open(os.path.join(os.path.dirname(__file__), "style.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
