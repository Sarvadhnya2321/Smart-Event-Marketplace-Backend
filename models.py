from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str  # user / organiser / vendor

class LoginRequest(BaseModel):
    email: str
    password: str

class EventCreate(BaseModel):
    organiser_id: int
    title: str
    description: str
    category: str
    location: str
    date: str
    budget: float
    ticket_price: float


class VendorCreate(BaseModel):
    user_id: int
    business_name: str
    category: str
    description: str
    price_range: str
    contact_info: str  # ✅ NEW


class VendorApplication(BaseModel):
    vendor_id: int
    event_id: int