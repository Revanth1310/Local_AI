import faiss
import numpy as np
import pickle
from pathlib import Path

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

FAISS_INDEX_PATH = BASE_DIR / "memory.index"
FAISS_MAPPING_PATH = BASE_DIR / "faiss_mapping.pkl"

DIMENSIONS = 384


# ------------------------------------------------------------
# CREATE INDEX
# ------------------------------------------------------------

def create_index():
    """
    Create a new empty FAISS index.
    """

    return faiss.IndexFlatIP(DIMENSIONS)


# ------------------------------------------------------------
# ADD VECTOR
# ------------------------------------------------------------

def add_vector(index, memory_id_mapping, memory_id, embedding):
    """
    Add one memory embedding to FAISS.

    memory_id_mapping stores:

        FAISS position -> SQLite memory ID
    """

    vector = np.array(
        [embedding],
        dtype="float32"
    )

    index.add(vector)

    memory_id_mapping.append(memory_id)


# ------------------------------------------------------------
# SAVE INDEX
# ------------------------------------------------------------

def save_index(index, memory_id_mapping):
    """
    Save FAISS index and SQLite-ID mapping to disk.
    """

    faiss.write_index(
        index,
        str(FAISS_INDEX_PATH)
    )

    with open(FAISS_MAPPING_PATH, "wb") as file:
        pickle.dump(
            memory_id_mapping,
            file
        )


# ------------------------------------------------------------
# LOAD INDEX
# ------------------------------------------------------------

def load_index():
    """
    Load FAISS index and memory ID mapping.
    """

    if not FAISS_INDEX_PATH.exists():
        return None, []

    index = faiss.read_index(
        str(FAISS_INDEX_PATH)
    )

    with open(FAISS_MAPPING_PATH, "rb") as file:
        memory_id_mapping = pickle.load(file)

    return index, memory_id_mapping
def search_index(index, memory_id_mapping, query_embedding, top_k=5):
    """
    Search FAISS using a query embedding.

    Returns:
        List of dictionaries containing:
        - memory_id
        - similarity
        - faiss_position
    """

    if index is None:
        return []

    if index.ntotal == 0:
        return []

    query_vector = np.array(
        [query_embedding],
        dtype="float32"
    )

    # Do not request more results than available vectors
    k = min(top_k, index.ntotal)

    distances, indices = index.search(
        query_vector,
        k
    )

    results = []

    for position, similarity in zip(
        indices[0],
        distances[0]
    ):
        # Safety check
        if position < 0:
            continue

        if position >= len(memory_id_mapping):
            continue

        memory_id = memory_id_mapping[position]

        results.append({
            "memory_id": memory_id,
            "similarity": float(similarity),
            "faiss_position": int(position)
        })

    return results
def rebuild_index():
    """
    Rebuild the FAISS index using all active SQLite memories.
    """

    from memory.database import get_all_memories
    from memory.embedding_store import get_embedding

    print("Rebuilding FAISS index...")

    memories = get_all_memories()

    index = create_index()

    memory_id_mapping = []

    for memory in memories:

        memory_id = memory["id"]

        embedding = get_embedding(memory_id)

        if embedding is None:
            print(
                f"Skipping memory {memory_id}: "
                "embedding not found."
            )
            continue

        add_vector(
            index,
            memory_id_mapping,
            memory_id,
            embedding
        )

    save_index(
        index,
        memory_id_mapping
    )

    print(
        f"FAISS rebuild complete. "
        f"Vectors: {index.ntotal}"
    )

    return index, memory_id_mapping