import math

from hand_tracking.database.db_operations import get_all_face_embeddings, get_professional_by_id


def cosine_similarity(vector_a, vector_b):
    """
    Returns cosine similarity for two equal-length numeric vectors.
    """
    if len(vector_a) != len(vector_b):
        raise ValueError("Embedding lengths must match.")

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def rank_matches(query_embedding, candidate_embeddings, top_k=3):
    """
    Returns the top-k candidate matches ranked by cosine similarity.
    """
    scored_matches = []

    for professional_id, embedding in candidate_embeddings:
        score = cosine_similarity(query_embedding, embedding)
        scored_matches.append((professional_id, score))

    scored_matches.sort(key=lambda item: item[1], reverse=True)
    return scored_matches[:top_k]


def find_best_database_matches(query_embedding, model_name, top_k=3):
    """
    Fetches embeddings from the database and returns ranked profile matches.
    """
    candidate_embeddings = get_all_face_embeddings(model_name)

    if not candidate_embeddings:
        return []

    ranked_ids = rank_matches(query_embedding, candidate_embeddings, top_k=top_k)
    matches = []

    for professional_id, score in ranked_ids:
        professional = get_professional_by_id(professional_id)
        if professional is not None:
            matches.append({
                "professional": professional,
                "score": score,
            })

    return matches
