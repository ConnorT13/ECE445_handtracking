import argparse
import os

from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import get_professional_by_id, upsert_face_embedding
from hand_tracking.matching.embedder import create_embedder


def parse_args():
    parser = argparse.ArgumentParser(
        description="Enroll a professional image into the face_embeddings table."
    )
    parser.add_argument("--professional-id", type=int, required=True, help="Professional ID from the database.")
    parser.add_argument("--image-path", required=True, help="Path to the professional headshot image.")
    parser.add_argument(
        "--backend",
        default="insightface",
        choices=["insightface", "mediapipe"],
        help="Embedding backend to use.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    initialize_database()

    professional = get_professional_by_id(args.professional_id)
    if professional is None:
        print(f"Professional id {args.professional_id} does not exist.")
        return

    image_path = args.image_path
    if not os.path.exists(image_path):
        print(f"Image path does not exist: {image_path}")
        return

    try:
        embedder = create_embedder(args.backend)
    except Exception as exc:
        print(f"Enrollment failed: {exc}")
        return
    try:
        result = embedder.embed_image_file(image_path)
    except Exception as exc:
        print(f"Enrollment failed: {exc}")
        return
    finally:
        embedder.close()

    upsert_face_embedding(args.professional_id, result.model_name, result.embedding)
    print(
        f"Stored embedding for {professional[1]} using model '{result.model_name}' "
        f"with dimension {len(result.embedding)}"
    )


if __name__ == "__main__":
    main()
