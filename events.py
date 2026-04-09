from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database import get_connection
from google.cloud import storage
import uuid

router = APIRouter()


# ---------- GCS UPLOAD ----------
def upload_to_gcs(file):
    client = storage.Client()
    bucket = client.bucket("smart-event-media-492714")

    filename = f"{uuid.uuid4()}_{file.filename}"
    blob = bucket.blob(filename)

    blob.upload_from_file(file.file, content_type=file.content_type)

    return f"https://storage.googleapis.com/{bucket.name}/{blob.name}"


# ---------- CREATE EVENT ----------
@router.post("/")
def create_event(
    organiser_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    location: str = Form(...),
    date: str = Form(...),
    budget: float = Form(...),
    ticket_price: float = Form(...),
    poster: UploadFile = File(...)
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        poster_url = upload_to_gcs(poster)

        cur.execute(
            """
            INSERT INTO events 
            (organiser_id, title, description, category, location, date, budget, ticket_price, poster_url, is_published)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s, TRUE)
            RETURNING id
            """,
            (
                organiser_id,
                title,
                description,
                category,
                location,
                date,
                budget,
                ticket_price,
                poster_url
            )
        )

        event_id = cur.fetchone()[0]
        conn.commit()

        return {
            "message": "Event created",
            "event_id": event_id,
            "poster_url": poster_url
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ---------- GET PUBLISHED EVENTS ----------
@router.get("/")
def get_published_events():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT 
                id,
                organiser_id,
                title,
                category,
                location,
                date,
                budget,
                ticket_price,
                poster_url,
                is_published
            FROM events
            WHERE is_published = TRUE
            ORDER BY date
            """
        )

        rows = cur.fetchall()

        # ✅ CONVERT TO JSON OBJECTS (CRITICAL FIX)
        events = [
            {
                "id": row[0],
                "organiser_id": row[1],
                "title": row[2],
                "category": row[3],
                "location": row[4],
                "date": row[5],
                "budget": row[6],
                "ticket_price": row[7],
                "poster_url": row[8],
                "is_published": row[9],
            }
            for row in rows
        ]

        return events

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ---------- GET APPLICATIONS ----------
@router.get("/{event_id}/applications")
def get_applications(event_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT va.id, v.business_name, v.category, va.status
            FROM vendor_applications va
            JOIN vendors v ON va.vendor_id = v.id
            WHERE va.event_id = %s
            """,
            (event_id,)
        )

        rows = cur.fetchall()

        applications = [
            {
                "id": row[0],
                "business_name": row[1],
                "category": row[2],
                "status": row[3]
            }
            for row in rows
        ]

        return applications

    finally:
        cur.close()
        conn.close()


# ---------- ACCEPT / REJECT ----------
@router.post("/applications/{app_id}/status")
def update_application_status(app_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE vendor_applications
            SET status = %s,
                is_selected = CASE WHEN %s = 'accepted' THEN TRUE ELSE FALSE END
            WHERE id = %s
            """,
            (status, status, app_id)
        )

        conn.commit()

        return {"message": f"Application {status}"}

    finally:
        cur.close()
        conn.close()


# ---------- PUBLISH EVENT ----------
@router.post("/{event_id}/publish")
def publish_event(event_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "UPDATE events SET is_published = TRUE WHERE id = %s",
            (event_id,)
        )

        conn.commit()

        return {"message": "Event published"}

    finally:
        cur.close()
        conn.close()

# ---------- DELETE EVENT ----------
@router.delete("/{event_id}")
def delete_event(event_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
        conn.commit()
        return {"message": "Event deleted"}
    finally:
        cur.close()
        conn.close()