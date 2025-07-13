import random
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_SENDER = os.getenv('EMAIL_SENDER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '465'))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'true').lower() == 'true'


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(to_email, otp):
    subject = 'Your OTP Code'
    body = f'Your OTP code is {otp}. It is valid for 10 minutes.'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    if EMAIL_USE_SSL:
        with smtplib.SMTP_SSL(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
    else:
        with smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
