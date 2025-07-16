import streamlit as st
import base64
import os

def set_bg_from_file(image_path: str):
    """Sets a background image for the Streamlit app from a local file (jpg/png)."""
    ext = os.path.splitext(image_path)[1][1:]
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
        encoded = base64.b64encode(img_bytes).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url('data:image/{ext};base64,{encoded}') no-repeat center center fixed;
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
