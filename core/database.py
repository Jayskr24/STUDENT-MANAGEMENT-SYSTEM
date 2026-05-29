import os
from pymongo import MongoClient

# Fall back to localhost only if MONGO_URI isn't defined in environment variables
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

def get_db():
    client = MongoClient(MONGO_URI)
    return client["school_manager"]

def init_db():
    # Optional initialize tracking hooks verification routine
    try:
        db = get_db()
        # Ping the database deployment cluster to verify access clearance
        db.command("ping")
        print("✅ MongoDB Context Connection Established Successfully!")
    except Exception as e:
        print(f"❌ Database Context Failure: {e}")