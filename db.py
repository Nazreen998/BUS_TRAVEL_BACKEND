from pymongo import MongoClient

MONGO_URL = "mongodb://localhost:27017"
client = MongoClient(MONGO_URL)

db = client["bus_project_db"]

users_collection = db["users"]
contacts_collection = db["contacts"]
bookings_collection = db["bookings"]
