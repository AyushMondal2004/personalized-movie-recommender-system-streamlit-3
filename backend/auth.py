import bcrypt
from .db import user_col, otp_col
from .utils import send_otp_email, generate_otp


def register_user(user_data):
    if user_col.find_one({'username': user_data['username']}):
        return False, 'Username already exists.'
    hashed_pw = bcrypt.hashpw(user_data['password'].encode(), bcrypt.gensalt())
    user_data['password'] = hashed_pw
    # Address is included in user_data if present
    user_col.insert_one(user_data)
    return True, 'Registration successful.'


def login_user(username, password):
    user = user_col.find_one({'username': username})
    if user and bcrypt.checkpw(password.encode(), user['password']):
        return True, user
    return False, 'Invalid username or password.'


def initiate_password_reset(email):
    user = user_col.find_one({'email': email})
    if not user:
        return False, 'Email not found.'
    otp = generate_otp()
    otp_col.insert_one({'email': email, 'otp': otp})
    send_otp_email(email, otp)
    return True, 'OTP sent to email.'


def reset_password(email, otp, new_password):
    record = otp_col.find_one({'email': email, 'otp': otp})
    if not record:
        return False, 'Invalid OTP.'
    hashed_pw = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    user_col.update_one({'email': email}, {'$set': {'password': hashed_pw}})
    otp_col.delete_many({'email': email})
    return True, 'Password reset successful.'
