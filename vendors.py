from fastapi import APIRouter, HTTPException
from database import get_connection
from models import VendorCreate, VendorApplication

router = APIRouter()


# ✅ REGISTER VENDOR PROFILE
@router.post("/register")
def register_vendor(vendor: VendorCreate):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO vendors 
            (user_id, business_name, category, description, price_range, contact_info)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                vendor.user_id,
                vendor.business_name,
                vendor.category,
                vendor.description,
                vendor.price_range,
                vendor.contact_info
            )
        )

        vendor_id = cur.fetchone()[0]
        conn.commit()

        return {
            "message": "Vendor registered successfully",
            "vendor_id": vendor_id
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ✅ APPLY TO EVENT
@router.post("/apply")
def apply_to_event(data: VendorApplication):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # check if already applied
        cur.execute(
            "SELECT 1 FROM vendor_applications WHERE vendor_id=%s AND event_id=%s",
            (data.vendor_id, data.event_id)
        )

        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Already applied")

        cur.execute(
            """
            INSERT INTO vendor_applications (vendor_id, event_id)
            VALUES (%s, %s)
            RETURNING id
            """,
            (data.vendor_id, data.event_id)
        )

        app_id = cur.fetchone()[0]
        conn.commit()

        return {
            "message": "Applied successfully",
            "application_id": app_id
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


# ✅ GET ALL VENDORS
@router.get("/")
def get_all_vendors():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT 
                id, 
                business_name, 
                category, 
                description, 
                price_range,
                contact_info
            FROM vendors
            ORDER BY id DESC
            """
        )

        vendors = [
            {
                "id": row[0],
                "business_name": row[1],
                "category": row[2],
                "description": row[3],
                "price_range": row[4],
                "contact_info": row[5],
            }
            for row in cur.fetchall()
        ]

        return vendors

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()


@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: int):
    conn = get_connection()
    cur = conn.cursor()

    try:
        # 🔍 Check if vendor exists
        cur.execute("SELECT id FROM vendors WHERE id = %s", (vendor_id,))
        vendor = cur.fetchone()

        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")

        # ❌ Delete related applications first (to avoid FK issues)
        cur.execute(
            "DELETE FROM vendor_applications WHERE vendor_id = %s",
            (vendor_id,)
        )

        # ❌ Delete vendor
        cur.execute(
            "DELETE FROM vendors WHERE id = %s",
            (vendor_id,)
        )

        conn.commit()

        return {"message": "Vendor deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cur.close()
        conn.close()