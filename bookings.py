from fastapi import APIRouter
from database import get_connection
import httpx
import asyncio

router = APIRouter()

# 🔔 Cloud Function URL
NOTIFY_URL = "PASTE_YOUR_FUNCTION_URL_HERE"


# ✅ CREATE BOOKING
@router.post("/")
def create_booking(user_id: int, event_id: int, tickets: int):
    conn = get_connection()
    cur = conn.cursor()

    # Calculate total amount
    cur.execute(
        "SELECT ticket_price FROM events WHERE id = %s",
        (event_id,)
    )
    result = cur.fetchone()

    if not result:
        return {"error": "Event not found"}

    ticket_price = result[0]
    total_amount = ticket_price * tickets

    # Insert booking
    cur.execute(
        """
        INSERT INTO bookings (user_id, event_id, tickets, total_amount)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (user_id, event_id, tickets, total_amount)
    )

    booking_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    # 🚀 CALL CLOUD FUNCTION
    async def send_notification(user_id, event_id):
        async with httpx.AsyncClient() as client:
            await client.post(NOTIFY_URL, json={
                "user_id": user_id,
                "event_id": event_id
            })

    try:
        asyncio.run(send_notification(user_id, event_id))
    except Exception as e:
        print("Notification error:", e)

    return {
        "message": "Booking successful",
        "booking_id": booking_id,
        "total_amount": total_amount
    }


# ✅ GET BOOKINGS FOR USER
@router.get("/{user_id}")
def get_user_bookings(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT b.id, e.title, b.tickets, b.total_amount, b.status
        FROM bookings b
        JOIN events e ON b.event_id = e.id
        WHERE b.user_id = %s
        """,
        (user_id,)
    )

    bookings = cur.fetchall()

    cur.close()
    conn.close()

    return bookings