import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USERNAME'),      
    'password': os.getenv('DB_PASSWORD'),  
    'database': os.getenv('DB_LOSTFOUND')
}

IMAGEKIT_CONFIG = {
    'private_key': os.getenv('IMAGE_PRIVATE_KEY'), 
    'public_key': os.getenv('IMAGE_PUBLIC_KEY'),  
    'url_endpoint': os.getenv('URI_ENDPOINT')   
}

SMTP_CONFIG = {
    'host': os.getenv('SMTP_HOST'),         # e.g., 'smtp.gmail.com'
    'port': int(os.getenv('SMTP_PORT')),    # e.g., 587 (for TLS) or 465 (for SSL)
    'sender_email': os.getenv('SMTP_USERNAME'), # Your Gmail address
    'sender_password': os.getenv('SMTP_PASSWORD') # Your Google App Password
}

