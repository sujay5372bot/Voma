# database.py
from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client['telegram_mirror_bot']

# Collections
users = db['users']
mirror_settings = db['mirror_settings']
sources = db['sources']
transactions = db['transactions']
withdrawals = db['withdrawals']
