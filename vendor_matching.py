from fastapi import APIRouter
from database import get_connection

router = APIRouter()

@router.get("/{event_id}")
def match_vendors(event_id: int):
    conn = get_connection()
    
    try:
        cur = conn.cursor()

        # 1. Get event category
        cur.execute(
            "SELECT category FROM events WHERE id = %s",
            (event_id,)
        )
        event = cur.fetchone()

        if not event:
            return {"error": "Event not found"}

        category = event[0]

        # 2. Get matching vendors ranked by highest rating
        cur.execute(
            """
            SELECT id, business_name, category, rating
            FROM vendors
            WHERE category = %s
            ORDER BY rating DESC
            """,
            (category,)
        )

        # 3. Map the raw database tuples into dictionaries for clean JSON output
        vendors = [
            {
                "id": row[0],
                "business_name": row[1],
                "category": row[2],
                "rating": row[3]
            }
            for row in cur.fetchall()
        ]

        return vendors

    finally:
        # Safely close connections even if an error is thrown
        if 'cur' in locals() and cur:
            cur.close()
        if conn:
            conn.close()