from memory.memory_store import MemoryStore
from memory.classifier import classify_memory
from memory.memory_scoring import (
    calculate_importance,
    calculate_confidence
)


class MemoryManager:

    def __init__(self, update_threshold=0.75):
        self.store = MemoryStore()
        self.update_threshold = update_threshold

    def remember(
        self,
        content,
        source="user"
    ):
        # 1. Classify memory
        memory_type = classify_memory(content)

        # 2. Calculate importance
        importance = calculate_importance(
            content,
            memory_type
        )

        # 3. Calculate confidence
        confidence = calculate_confidence(content)

        # 4. Search existing memories
        results = self.store.search(
            content,
            top_k=5
        )

        # 5. No existing memory → CREATE
        if not results:

            memory_id = self.store.save(
                content=content,
                memory_type=memory_type,
                importance=importance,
                confidence=confidence,
                source=source
            )

            return {
                "action": "created",
                "memory_id": memory_id,
                "memory_type": memory_type,
                "importance": importance,
                "confidence": confidence,
                "content": content
            }

        # 6. Get closest memory
        best_match = results[0]

        similarity = best_match["similarity"]
        existing_id = best_match["memory_id"]

        # 7. Similar enough → UPDATE
        if similarity >= self.update_threshold:

            success = self.store.update(
                existing_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                confidence=confidence,
                source=source
            )

            return {
                "action": "updated",
                "memory_id": existing_id,
                "memory_type": memory_type,
                "importance": importance,
                "confidence": confidence,
                "similarity": similarity,
                "content": content,
                "success": success
            }

        # 8. Different → CREATE
        memory_id = self.store.save(
            content=content,
            memory_type=memory_type,
            importance=importance,
            confidence=confidence,
            source=source
        )

        return {
            "action": "created",
            "memory_id": memory_id,
            "memory_type": memory_type,
            "importance": importance,
            "confidence": confidence,
            "similarity": similarity,
            "content": content
        }