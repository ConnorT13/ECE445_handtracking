import sqlite3
from .db_init import get_database_path


def add_professional(
    name,
    title,
    organization=None,
    quantum_area=None,
    short_bio=None,
    long_bio=None,
    image_path=None,
    fun_fact=None,
    video_url=None
):
    """
    Inserts a professional profile into the database.
    Returns the new professional ID.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO professionals (
            name, title, organization, quantum_area,
            short_bio, long_bio, image_path, fun_fact, video_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, title, organization, quantum_area,
        short_bio, long_bio, image_path, fun_fact, video_url
    ))

    professional_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return professional_id


def add_tag_to_professional(professional_id, tag):
    """
    Adds a tag to a professional profile.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO profile_tags (professional_id, tag)
        VALUES (?, ?)
    """, (professional_id, tag))

    connection.commit()
    connection.close()


def get_all_professionals():
    """
    Returns all professional profiles.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, title, organization, quantum_area,
               short_bio, long_bio, image_path, fun_fact, video_url, created_at
        FROM professionals
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_professional_by_id(professional_id):
    """
    Returns one professional profile by ID.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, title, organization, quantum_area,
               short_bio, long_bio, image_path, fun_fact, video_url, created_at
        FROM professionals
        WHERE id = ?
    """, (professional_id,))

    row = cursor.fetchone()
    connection.close()

    return row


def get_tags_for_professional(professional_id):
    """
    Returns all tags for a given professional.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT tag
        FROM profile_tags
        WHERE professional_id = ?
        ORDER BY tag ASC
    """, (professional_id,))

    rows = cursor.fetchall()
    connection.close()

    return [row[0] for row in rows]


def get_professionals_by_tag(tag):
    """
    Returns professionals that have a specific tag.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT p.id, p.name, p.title, p.organization, p.quantum_area,
               p.short_bio, p.long_bio, p.image_path, p.fun_fact, p.video_url, p.created_at
        FROM professionals p
        JOIN profile_tags t ON p.id = t.professional_id
        WHERE t.tag = ?
        ORDER BY p.name ASC
    """, (tag,))

    rows = cursor.fetchall()
    connection.close()

    return rows


def log_interaction(event_type, matched_professional_id=None, notes=None):
    """
    Logs an interaction or match event.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO interaction_logs (event_type, matched_professional_id, notes)
        VALUES (?, ?, ?)
    """, (event_type, matched_professional_id, notes))

    connection.commit()
    connection.close()


def get_recent_logs(limit=10):
    """
    Returns the most recent interaction logs.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, event_type, matched_professional_id, notes, created_at
        FROM interaction_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    connection.close()

    return rows