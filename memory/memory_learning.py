from memory.memory_extractor import extract_memories
from memory.memory_manager import MemoryManager


class MemoryLearning:
    """
    Converts conversations into long-term memories.
    """

    def __init__(self):
        self.manager = None

    def learn_from_conversation(self, user_message, assistant_response):
        memories = extract_memories(
            user_message,
            assistant_response
        )

        if not memories:
            return []

        if self.manager is None:
            self.manager = MemoryManager()

        results = []

        for memory in memories:
            result = self.manager.remember(
                memory,
                source="conversation"
            )

            results.append({
                "memory": memory,
                "result": result
            })

        return results
    