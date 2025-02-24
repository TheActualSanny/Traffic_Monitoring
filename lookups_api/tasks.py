'''
    In order for the user to be authorized, the API uses a JSON Web Token as the API Key. 
    which is essential to send requests to the endpoints.
    The API Key will be sent to the user on his/her email.
'''
import smtplib
import ssl
import re
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import shared_task

load_dotenv()

@shared_task
def send_key(api_key: str, user_email: str) -> None:
    '''
        In our case, we are using a secure SSL connection to send the API Key.
    '''

    sender_email, sender_password = os.getenv('EMAIL'), os.getenv('PASSWORD')
    context = ssl.create_default_context()
    message = MIMEMultipart()
    message['Subject'] = 'OSINT Collection API Key'
    message['From'] = sender_email
    message['To'] = user_email
    text_content = MIMEText(f'Your API Key: {api_key}', 'plain')
    message.attach(text_content)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context = context) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, user_email, message.as_string())
