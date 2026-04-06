import argparse

from hand_tracking.database.db_init import initialize_database
from hand_tracking.matching.embedder import create_embedder
from hand_tracking.matching.match import find_best_database_matches


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query the database for the top face matches from a still image."
    )
    parser.add_argument("--image-path", required=True, help="Path to a query image containing one face.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of matches to return.")
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

    try:
        embedder = create_embedder(args.backend)
    except Exception as exc:
        print(f"Query failed: {exc}")
        return
    try:
        result = embedder.embed_image_file(args.image_path)
    except Exception as exc:
        print(f"Query failed: {exc}")
        return
    finally:
        embedder.close()

    matches = find_best_database_matches(result.embedding, result.model_name, top_k=args.top_k)
    if not matches:
        print(
            f"No embeddings found for model '{result.model_name}'. "
            "Enroll professional images first."
        )
        return

    print("Top matches:")
    for index, match in enumerate(matches, start=1):
        professional = match["professional"]
        print(f"{index}. {professional[1]} - score={match['score']:.4f}")


if __name__ == "__main__":
    main()
