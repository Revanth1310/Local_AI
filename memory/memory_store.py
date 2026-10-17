from memory.database import (
    initialize_database,
    save_memory,
    get_memory,
    get_all_memories,
    get_memory_history,
    update_memory,
    delete_memory
)

from memory.search import search_memory


class MemoryStore:
    """
    High-level interface for the long-term memory system.

    This class hides the implementation details of:
        - SQLite
        - BGE embeddings
        - FAISS
    """

    def __init__(self):
        print("Initializing MemoryStore...")
        initialize_database()
        print("MemoryStore ready.")

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    def save(
        self,
        content,
        memory_type="general",
        importance=0.5,
        confidence=1.0,
        source=None
    ):
        """
        Save a new memory.
        """

        return save_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            source=source
        )

    # --------------------------------------------------------
    # READ ONE
    # --------------------------------------------------------

    def get(self, memory_id):
        """
        Get one active memory by ID.
        """

        return get_memory(memory_id)

    # --------------------------------------------------------
    # READ ALL
    # --------------------------------------------------------

    def get_all(self):
        """
        Get all active memories.
        """

        return get_all_memories()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    def search(self, query, top_k=5):
        """
        Search memories semantically.
        """

        return search_memory(
            query,
            top_k=top_k
        )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(
        self,
        memory_id,
        content=None,
        memory_type=None,
        importance=None,
        confidence=None,
        source=None
    ):
        """
        Update an existing memory.
        """

        return update_memory(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            source=source
        )

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    def delete(self, memory_id):
        """
        Soft-delete a memory.
        """

        return delete_memory(memory_id)

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    def history(self, memory_id):
        """
        Get complete history of a memory.
        """

        return get_memory_history(memory_id)