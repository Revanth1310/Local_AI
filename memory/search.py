from memory.embeddings import create_embedding
from memory.faiss_store import load_index, search_index
from memory.database import get_memory


def search_memory(
    query,
    top_k=5,
    memory_type=None,
    min_importance=None,
    min_confidence=None
):
    """
    Search memories using semantic similarity,
    then rerank and optionally filter results.
    """

    index, memory_id_mapping = load_index()

    if index is None:
        return []

    query_embedding = create_embedding(query)

    # Retrieve extra candidates before filtering
    candidate_count = max(top_k * 3, 10)

    results = search_index(
        index,
        memory_id_mapping,
        query_embedding,
        top_k=candidate_count
    )

    ranked_results = []

    for result in results:

        memory_id = result["memory_id"]

        memory = get_memory(memory_id)

        if memory is None:
            continue

        # -------------------------
        # Filters
        # -------------------------

        if memory_type is not None:
            if memory["memory_type"] != memory_type:
                continue

        if min_importance is not None:
            if memory["importance"] < min_importance:
                continue

        if min_confidence is not None:
            if memory["confidence"] < min_confidence:
                continue

        # -------------------------
        # Ranking
        # -------------------------

        similarity = result["similarity"]
        importance = memory["importance"]
        confidence = memory["confidence"]

        final_score = (
            0.70 * similarity
            + 0.20 * importance
            + 0.10 * confidence
        )

        ranked_results.append({
            "memory_id": memory_id,
            "content": memory["content"],
            "memory_type": memory["memory_type"],
            "importance": importance,
            "confidence": confidence,
            "similarity": similarity,
            "final_score": final_score
        })

    # Sort by final score
    ranked_results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return ranked_results[:top_k]