import os
import sqlite3


def get_database_path():
    """
    Returns the absolute path to the SQLite database file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, "mirror.db")


def initialize_database():
    """
    Creates the database and required tables if they do not already exist.
    """
    db_path = get_database_path()
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS professionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            organization TEXT,
            quantum_area TEXT,
            short_bio TEXT,
            long_bio TEXT,
            image_path TEXT,
            fun_fact TEXT,
            video_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professional_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interaction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            matched_professional_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (matched_professional_id) REFERENCES professionals(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professional_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professional_id, model_name),
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS demo_profile_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_professional_id INTEGER NOT NULL UNIQUE,
            target_professional_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_professional_id) REFERENCES professionals(id),
            FOREIGN KEY (target_professional_id) REFERENCES professionals(id)
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
