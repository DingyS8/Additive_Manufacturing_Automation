import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()
_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
_db = _client[os.getenv("MONGO_DB", "converte_ai")]

def get_db():
    return _db

def ensure_indexes():
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.orders.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    db.payments.create_index([("order_id", ASCENDING)])
    db.files.create_index([("owner_id", ASCENDING), ("created_at", ASCENDING)])
