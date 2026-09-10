"""Creates the schema (if missing) and loads demo data.

Usage: uv run python seed.py
Safe to re-run against an existing DB — it skips seeding if demo users
already exist, but always ensures the schema is present.
"""

from app.db import encode_amenities, execute, get_connection, init_schema, query_one
from app.security import hash_password

DEMO_OWNER_EMAIL = "owner@spacematch.demo"
DEMO_BOOKER_EMAIL = "booker@spacematch.demo"
DEMO_PASSWORD = "password123"


def seed() -> None:
    conn = get_connection()
    init_schema(conn)

    if query_one(conn, "SELECT id FROM users WHERE email = ?", (DEMO_OWNER_EMAIL,)):
        print("Demo data already present, skipping.")
        conn.close()
        return

    owner_id = execute(
        conn,
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ("Demo Owner", DEMO_OWNER_EMAIL, hash_password(DEMO_PASSWORD), "owner"),
    )
    execute(
        conn,
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        ("Demo Booker", DEMO_BOOKER_EMAIL, hash_password(DEMO_PASSWORD), "booker"),
    )

    spaces = [
        {
            "name": "Riverside Coworking",
            "address": "12 Riverside Lane, Berlin",
            "contact_info": "hello@riverside-coworking.demo",
            "description": "A converted warehouse with several bookable rooms near the river.",
            "rooms": [
                {
                    "name": "The Quiet Corner",
                    "capacity": 2,
                    "price": 15,
                    "price_unit": "hour",
                    "amenities": ["wifi"],
                    "notes": "Small, quiet corner room with natural light from a big window. "
                    "No phone booth nearby, ideal for focused solo work or a 1:1 call.",
                },
                {
                    "name": "Workshop Hall",
                    "capacity": 20,
                    "price": 220,
                    "price_unit": "day",
                    "amenities": ["wifi", "projector", "whiteboard", "ac"],
                    "notes": "Big open hall with movable furniture, great acoustics, and a lot "
                    "of natural light. Popular for full-day workshops and trainings.",
                },
                {
                    "name": "Boardroom North",
                    "capacity": 8,
                    "price": 60,
                    "price_unit": "hour",
                    "amenities": ["wifi", "projector", "whiteboard"],
                    "notes": "Formal boardroom with a long table, good for client-facing "
                    "meetings. Can feel a bit sterile for creative sessions.",
                },
            ],
        },
        {
            "name": "Green Loft Studios",
            "address": "88 Park Avenue, Berlin",
            "contact_info": "bookings@greenloft.demo",
            "description": "Plant-filled loft space with a relaxed, creative atmosphere.",
            "rooms": [
                {
                    "name": "The Greenhouse",
                    "capacity": 6,
                    "price": 40,
                    "price_unit": "hour",
                    "amenities": ["wifi", "kitchen"],
                    "notes": "Sunny room full of plants, very calm atmosphere, popular for "
                    "creative brainstorms and small team offsites. Has a small kitchen nook.",
                },
                {
                    "name": "Loft Studio A",
                    "capacity": 12,
                    "price": 150,
                    "price_unit": "day",
                    "amenities": ["wifi", "projector", "kitchen", "ac"],
                    "notes": "Open-plan loft with exposed brick and skylights. Good energy for "
                    "workshops, though it can get loud when the street market is on.",
                },
            ],
        },
        {
            "name": "Harborview Business Center",
            "address": "3 Harbor Street, Hamburg",
            "contact_info": "info@harborview.demo",
            "description": "Professional business center near the harbor with formal meeting rooms.",
            "rooms": [
                {
                    "name": "Executive Suite",
                    "capacity": 10,
                    "price": 90,
                    "price_unit": "hour",
                    "amenities": ["wifi", "projector", "whiteboard", "ac", "parking"],
                    "notes": "High-end meeting room with harbor views, ideal for investor "
                    "pitches and client presentations. On-site parking available.",
                },
                {
                    "name": "Focus Pod",
                    "capacity": 1,
                    "price": 8,
                    "price_unit": "hour",
                    "amenities": ["wifi"],
                    "notes": "Single-person soundproof pod for calls or deep focus work. "
                    "Very quiet, no windows.",
                },
                {
                    "name": "Training Room B",
                    "capacity": 16,
                    "price": 180,
                    "price_unit": "day",
                    "amenities": ["wifi", "projector", "whiteboard", "ac", "parking"],
                    "notes": "Classroom-style training room with individual desks and plenty "
                    "of parking. Slightly institutional feel.",
                },
            ],
        },
    ]

    for space in spaces:
        space_id = execute(
            conn,
            "INSERT INTO spaces (owner_id, name, address, contact_info, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (owner_id, space["name"], space["address"], space["contact_info"], space["description"]),
        )
        for room in space["rooms"]:
            execute(
                conn,
                "INSERT INTO rooms (space_id, name, capacity, price, price_unit, amenities, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    space_id,
                    room["name"],
                    room["capacity"],
                    room["price"],
                    room["price_unit"],
                    encode_amenities(room["amenities"]),
                    room["notes"],
                ),
            )

    conn.close()
    print("Seeded demo data.")
    print(f"  Owner login:  {DEMO_OWNER_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Booker login: {DEMO_BOOKER_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    seed()
