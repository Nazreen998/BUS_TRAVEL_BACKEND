import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)

db = client["bus_project_db"]

users_collection = db["users"]
contacts_collection = db["contacts"]
bookings_collection = db["bookings"]