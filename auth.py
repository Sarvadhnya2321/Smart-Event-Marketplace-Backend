import hashlib
from fastapi import APIRouter, HTTPException
from database import get_connection
from models import UserCreate, LoginRequest

router = APIRouter()

# REGISTER
@router.post("/register")
def register(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor()

    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

    try:
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user.name, user.email, hashed_password, user.role)
        )

        user_id = cur.fetchone()[0]
        conn.commit()

        return {"message": "User registered", "user_id": user_id}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    finally:
        cur.close()
        conn.close()


# LOGIN
@router.post("/login")
def login(data: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    hashed_password = hashlib.sha256(data.password.encode()).hexdigest()

    cur.execute(
        """
        SELECT id, name, role, password_hash
        FROM users
        WHERE email = %s
        """,
        (data.email,)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if hashed_password != user[3]:
        raise HTTPException(status_code=401, detail="Wrong password")

    return {
        "user_id": user[0],
        "name": user[1],
        "role": user[2]
    }