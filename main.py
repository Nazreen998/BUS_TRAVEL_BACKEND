from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from db import users_collection, contacts_collection
from models import RegisterUser, LoginUser, ContactMessage, ResetPassword
from auth import hash_password, verify_password, create_access_token
from db import users_collection, contacts_collection, bookings_collection
from models import RegisterUser, LoginUser, ContactMessage, ResetPassword, BookingRequest
from bson import ObjectId
from models import CancelBooking,HistoryRequest

app = FastAPI()

origins=["https://bus-travel-backend.onrender.com"]

# Allow frontend HTML to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API working"}

@app.post("/booking-history")
def booking_history(data: HistoryRequest):

    bookings = list(
        bookings_collection.find(
            {"username": data.username},
            {"_id": 1, "route": 1, "seats": 1, "status": 1, "createdAt": 1}
        ).sort("createdAt", -1)
    )

    for b in bookings:
        b["_id"] = str(b["_id"])

    return bookings
@app.post("/book-seat")
def book_seat(data: BookingRequest):

    # 1️⃣ user check
    user = users_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not data.seats:
        raise HTTPException(status_code=400, detail="Seats required")

    # 2️⃣ SAME USER – pending booking check
    existing_pending = bookings_collection.find_one({
        "username": data.username,
        "route": data.route,
        "status": "PENDING_PAYMENT"
    })

    if existing_pending:
        return {
            "message": "Already booking pending 💳",
            "booking_id": str(existing_pending["_id"]),
            "status": "PENDING_PAYMENT"
        }

    # 3️⃣ SEAT already booked check
    seat_taken = bookings_collection.find_one({
        "route": data.route,
        "status": {"$in": ["PENDING_PAYMENT", "CONFIRMED"]},
        "seats": {"$in": data.seats}
    })

    if seat_taken:
        raise HTTPException(
            status_code=400,
            detail="Some seats already booked ❌"
        )

    # 4️⃣ create new booking
    doc = {
        "username": data.username,
        "route": data.route,
        "seats": data.seats,
        "status": "PENDING_PAYMENT",
        "createdAt": datetime.utcnow()
    }

    result = bookings_collection.insert_one(doc)

    return {
        "message": "Booking saved ✅",
        "booking_id": str(result.inserted_id),
        "status": "PENDING_PAYMENT"
    }
@app.get("/booked-seats/{route}")
def get_booked_seats(route: str):

    bookings = bookings_collection.find({
        "route": route,
        "status": {"$in": ["PENDING_PAYMENT", "CONFIRMED"]}
    })

    booked = set()

    for b in bookings:
        for s in b["seats"]:
            booked.add(s)

    return {"bookedSeats": list(booked)}

@app.post("/cancel-booking")
def cancel_booking(data: CancelBooking):

    booking = bookings_collection.find_one({
        "_id": ObjectId(data.booking_id),
        "username": data.username
    })

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking["status"] == "CANCELLED":
        raise HTTPException(status_code=400, detail="Ticket already cancelled")

    bookings_collection.update_one(
        {"_id": ObjectId(data.booking_id)},
        {"$set": {
            "status": "CANCELLED",
            "cancelledAt": datetime.utcnow()
        }}
    )

    return {"message": "Ticket cancelled successfully ❌"}

@app.post("/book-seat")
def book_seat(data: BookingRequest):

    # user check
    user = users_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # seats empty check
    if not data.seats:
        raise HTTPException(status_code=400, detail="Seats required")

    doc = {
        "username": data.username,
        "route": data.route,
        "seats": data.seats,
        "status": "PENDING_PAYMENT",
        "createdAt": datetime.utcnow()
    }

    result = bookings_collection.insert_one(doc)

    return {
        "message": "Booking saved ✅",
        "booking_id": str(result.inserted_id)
    }

@app.get("/")
def home():
    return {"message": "Bus Project Backend Running 🚍🔥"}


# ✅ Register API
@app.post("/register")
def register(user: RegisterUser):

    # username check
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    # email check
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    # bcrypt max length check
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password max 72 characters only")

    new_user = {
        "name": user.name,
        "email": user.email,
        "username": user.username,
        "passwordHash": hash_password(user.password),
        "createdAt": datetime.utcnow()
    }

    users_collection.insert_one(new_user)

    return {"message": "User registered successfully ✅"}


# ✅ Login API
@app.post("/login")
def login(user: LoginUser):

    db_user = users_collection.find_one({"username": user.username})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(user.password, db_user["passwordHash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({
        "username": db_user["username"],
        "email": db_user["email"]
    })

    return {
        "message": "Login success ✅",
        "access_token": token,
        "token_type": "bearer",
        "username": db_user["username"]
    }


# ✅ Reset Password API
@app.post("/reset-password")
def reset_password(data: ResetPassword):

    user = users_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(data.new_password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password max 72 characters only")

    users_collection.update_one(
        {"username": data.username},
        {"$set": {"passwordHash": hash_password(data.new_password)}}
    )

    return {"message": "Password reset success ✅"}


# ✅ Contact Form Save API
@app.post("/contact")
def contact(data: ContactMessage):

    doc = {
        "name": data.name,
        "email": data.email,
        "message": data.message,
        "createdAt": datetime.utcnow()
    }

    contacts_collection.insert_one(doc)

    return {"message": "Message saved ✅"}
