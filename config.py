# config.py
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
USER_SESSION_STRING = os.getenv('USER_SESSION_STRING')  # Session string from a user account
MONGO_URI = os.getenv('MONGO_URI')
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_IDS', '').split(',') if x]  # Comma-separated admin user IDs
MIN_WITHDRAW = 100.0  # Minimum withdrawal amount
PLANS = {
    'basic': {'price': 100, 'days': 30},
    'pro': {'price': 200, 'days': 90},
    'ultra': {'price': 300, 'days': 365}
}
