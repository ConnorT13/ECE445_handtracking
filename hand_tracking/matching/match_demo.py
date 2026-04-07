from hand_tracking.database.db_init import initialize_database
from hand_tracking.database.db_operations import get_all_professionals
from hand_tracking.matching.bootstrap_mock_embeddings import MODEL_NAME, generate_mock_embedding
from hand_tracking.matching.match import find_best_database_matches


def main():
    initialize_database()

    professionals = get_all_professionals()
    if not professionals:
        print("No professionals found. Run seed_dummy_professionals.py first.")
        return

    reference_professional = professionals[0]
    name = reference_professional[1]
    quantum_area = reference_professional[4] or ""
    query_embedding = generate_mock_embedding(f"{name}|{quantum_area}")

    matches = find_best_database_matches(query_embedding, MODEL_NAME, top_k=3)
    if not matches:
        print("No embeddings found. Run matching/bootstrap_mock_embeddings.py first.")
        return

    print("Top matches:")
    for index, match in enumerate(matches, start=1):
        professional = match["professional"]
        print(f"{index}. {professional[1]} - score={match['score']:.4f}")


if __name__ == "__main__":
    main()
