import os
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import (
    get_all_professionals,
    update_professional_image_path,
    upsert_face_embedding,
)
from hand_tracking.database.path_utils import normalize_image_path_for_storage, resolve_image_path
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
            stored_image_path = professional[7]
            resolved_image_path = resolve_image_path(stored_image_path)

            if resolved_image_path is None:
                print(f"Skipping {name}: missing image path '{stored_image_path}'")
                skipped_count += 1
                continue

            normalized_path = normalize_image_path_for_storage(resolved_image_path)
            if normalized_path != stored_image_path:
                update_professional_image_path(professional_id, normalized_path)
                print(f"Updated {name} image path -> {normalized_path}")

            try:
                result = embedder.embed_image_file(resolved_image_path)
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
