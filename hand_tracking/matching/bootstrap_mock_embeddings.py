import hashlib

from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import get_all_professionals, upsert_face_embedding


MODEL_NAME = "mock-face-v1"
EMBEDDING_DIMENSION = 16


def generate_mock_embedding(seed_text, dimension=EMBEDDING_DIMENSION):
    """
    Builds a deterministic pseudo-embedding from text for pipeline testing.
    """
    values = []

    for index in range(dimension):
        digest = hashlib.sha256(f"{seed_text}:{index}".encode("utf-8")).digest()
        raw_value = int.from_bytes(digest[:4], byteorder="big", signed=False)
        normalized_value = (raw_value / 4294967295.0) * 2.0 - 1.0
        values.append(normalized_value)

    return values


def main():
    initialize_database()
    professionals = get_all_professionals()

    for professional in professionals:
        professional_id = professional[0]
        name = professional[1]
        quantum_area = professional[4] or ""
        embedding = generate_mock_embedding(f"{name}|{quantum_area}")
        upsert_face_embedding(professional_id, MODEL_NAME, embedding)

    print(f"Stored {len(professionals)} mock embeddings using model '{MODEL_NAME}'")


if __name__ == "__main__":
    main()
