from pydantic import BaseModel, EmailStr
from typing import List

class BookingRequest(BaseModel):
    username: str
    route: str
    seats: List[int]
    travel_date: str
    
class CancelBooking(BaseModel):
    booking_id: str
    username: str

class HistoryRequest(BaseModel):
    username: str

class RegisterUser(BaseModel):
    name: str
    email: EmailStr
    username: str
    password: str


class LoginUser(BaseModel):
    username: str
    password: str


class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str


class ResetPassword(BaseModel):
    username: str
    new_password: str
