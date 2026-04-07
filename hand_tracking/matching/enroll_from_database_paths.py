import os

from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import get_all_professionals, upsert_face_embedding
from hand_tracking.matching.embedder import create_embedder


def main():
    initialize_database()
    professionals = get_all_professionals()
    try:
        embedder = create_embedder("insightface")
    except Exception as exc:
        print(f"Enrollment failed: {exc}")
        return

    enrolled_count = 0
    skipped_count = 0

    try:
        for professional in professionals:
            professional_id = professional[0]
            name = professional[1]
            image_path = professional[7]

            if not image_path or not os.path.exists(image_path):
                print(f"Skipping {name}: missing image path '{image_path}'")
                skipped_count += 1
                continue

            try:
                result = embedder.embed_image_file(image_path)
                upsert_face_embedding(professional_id, result.model_name, result.embedding)
                print(f"Enrolled {name}")
                enrolled_count += 1
            except Exception as exc:
                print(f"Skipping {name}: {exc}")
                skipped_count += 1
    finally:
        embedder.close()

    print(f"Finished enrollment. enrolled={enrolled_count} skipped={skipped_count}")


if __name__ == "__main__":
    main()
