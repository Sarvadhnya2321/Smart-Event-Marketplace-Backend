from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from events import router as event_router
from vendors import router as vendor_router 
from bookings import router as booking_router
from vendor_matching import router as vm_router
from recommendations import router as rec_router

app = FastAPI()

# 1. Explicitly list the URLs that are allowed to talk to your backend
origins = [
    "http://localhost:5173",       # Local React development
    "http://136.115.236.33:3000",   # Your Cloud VM Public IP
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # 2. Use the explicit list instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(event_router, prefix="/events")
app.include_router(vendor_router, prefix="/vendors")
app.include_router(booking_router, prefix="/bookings")
app.include_router(vm_router, prefix="/vendor-matching")
app.include_router(rec_router, prefix="/recommendations")

@app.get("/")
def root():
    return {"message": "Smart Event Backend running 🚀"}