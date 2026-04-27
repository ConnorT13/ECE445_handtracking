import json
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


def get_professional_by_name(name):
    """
    Returns one professional profile by name.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, title, organization, quantum_area,
               short_bio, long_bio, image_path, fun_fact, video_url, created_at
        FROM professionals
        WHERE name = ?
    """, (name,))

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


def get_professionals_by_quantum_area(quantum_area):
    """
    Returns professionals for a given quantum area (primary column or profile_tags).
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT DISTINCT id, name, title, organization, quantum_area,
               short_bio, long_bio, image_path, fun_fact, video_url, created_at
        FROM professionals
        WHERE quantum_area = ?
           OR id IN (SELECT professional_id FROM profile_tags WHERE tag = ?)
        ORDER BY name ASC
    """, (quantum_area, quantum_area))

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_all_career_areas():
    """
    Returns all unique career areas from both quantum_area column and profile_tags.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT quantum_area FROM professionals WHERE quantum_area IS NOT NULL")
    areas = {row[0] for row in cursor.fetchall()}

    cursor.execute("SELECT DISTINCT tag FROM profile_tags")
    areas |= {row[0] for row in cursor.fetchall()}

    connection.close()
    return areas


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


def upsert_face_embedding(professional_id, model_name, embedding):
    """
    Inserts or updates a face embedding for a professional/model pair.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    embedding_json = json.dumps(embedding)

    cursor.execute("""
        INSERT INTO face_embeddings (professional_id, model_name, embedding_json)
        VALUES (?, ?, ?)
        ON CONFLICT(professional_id, model_name)
        DO UPDATE SET embedding_json = excluded.embedding_json
    """, (professional_id, model_name, embedding_json))

    connection.commit()
    connection.close()


def get_face_embedding(professional_id, model_name):
    """
    Returns a decoded embedding list for a professional/model pair.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT embedding_json
        FROM face_embeddings
        WHERE professional_id = ? AND model_name = ?
    """, (professional_id, model_name))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return json.loads(row[0])


def get_all_face_embeddings(model_name):
    """
    Returns all embeddings for a given model name.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT professional_id, embedding_json
        FROM face_embeddings
        WHERE model_name = ?
        ORDER BY professional_id ASC
    """, (model_name,))

    rows = cursor.fetchall()
    connection.close()

    return [(professional_id, json.loads(embedding_json)) for professional_id, embedding_json in rows]


def set_demo_profile_link(source_professional_id, target_professional_id):
    """
    Points a source professional to a target profile for demo display.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO demo_profile_links (source_professional_id, target_professional_id)
        VALUES (?, ?)
        ON CONFLICT(source_professional_id)
        DO UPDATE SET target_professional_id = excluded.target_professional_id
    """, (source_professional_id, target_professional_id))

    connection.commit()
    connection.close()


def get_demo_profile_target(source_professional_id):
    """
    Returns the linked target professional row if one exists, otherwise None.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT p.id, p.name, p.title, p.organization, p.quantum_area,
               p.short_bio, p.long_bio, p.image_path, p.fun_fact, p.video_url, p.created_at
        FROM demo_profile_links d
        JOIN professionals p ON p.id = d.target_professional_id
        WHERE d.source_professional_id = ?
    """, (source_professional_id,))

    row = cursor.fetchone()
    connection.close()

    return row
