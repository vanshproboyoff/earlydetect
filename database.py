import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "earlydetect.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'User',
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            overall_level TEXT,
            high_count INTEGER,
            moderate_count INTEGER,
            risk_profile TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def create_user(name, username, password):
    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO users (name, username, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                username,
                generate_password_hash(password)
            )
        )

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def verify_user(username, password):
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):
        return user

    return None


def save_screening(user_id, risk_profile, date):
    conn = get_db()

    conn.execute("""
        INSERT INTO screenings
        (
            user_id,
            date,
            overall_level,
            high_count,
            moderate_count,
            risk_profile
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        date,
        risk_profile.get("overall_level"),
        risk_profile.get("high_count", 0),
        risk_profile.get("moderate_count", 0),
        str(risk_profile)
    ))

    conn.commit()
    conn.close()


def get_screenings(user_id):
    conn = get_db()

    results = conn.execute("""
        SELECT *
        FROM screenings
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return results