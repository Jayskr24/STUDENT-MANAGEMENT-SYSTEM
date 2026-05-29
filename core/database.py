import os
from pymongo import MongoClient

# Looks for a cloud connection string first; defaults to local if not found
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

def get_db():
    client = MongoClient(MONGO_URI)
    return client["school_manager"]

def init_db():
    """Verifies connection health to the local MongoDB server instance."""
    try:
        db = get_db()
        db.command("ping")
        print("🍃 Successfully connected to local MongoDB Server!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed! Ensure MongoDB is running.\nError: {e}")