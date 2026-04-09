from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.get("/{user_id}")
def recommend_events(user_id: int):
    conn = get_connection()
    
    try:
        cur = conn.cursor()

        # 1. Get categories the user has booked
        cur.execute(
            """
            SELECT e.category
            FROM bookings b
            JOIN events e ON b.event_id = e.id
            WHERE b.user_id = %s
            """,
            (user_id,)
        )

        categories = [row[0] for row in cur.fetchall()]

        if not categories:
            return []

        # 2. Recommend other published events in those same categories
        cur.execute(
            """
            SELECT id, title, location, ticket_price, poster_url
            FROM events
            WHERE category = ANY(%s)
            AND is_published = TRUE
            """,
            (categories,)
        )

        # 3. Map the raw database tuples into dictionaries for clean JSON output
        events = [
            {
                "id": row[0],
                "title": row[1],
                "location": row[2],
                "ticket_price": row[3],
                "poster_url": row[4]
            }
            for row in cur.fetchall()
        ]

        return events

    finally:
        # Using a finally block ensures connections close even if an error occurs
        if cur:
            cur.close()
        if conn:
            conn.close()