from concurrent.futures import ThreadPoolExecutor
import re

from memory.memory_store import MemoryStore
from memory.context_builder import build_memory_context
from memory.conversation_store import (
    initialize_conversation_table,
    save_conversation
)
from memory.memory_learning import MemoryLearning
from model.llm import ask_qwen


class MemoryChat:

    def __init__(
        self,
        top_k=5,
        num_predict=512,
        think=False
    ):
        print("Initializing MemoryChat...")

        # Memory system
        self.store = MemoryStore()

        initialize_conversation_table()

        self.memory_learning = MemoryLearning()

        self.top_k = top_k

        # AI generation settings
        self.num_predict = num_predict
        self.think = think

        # Background processing
        self.executor = ThreadPoolExecutor(
            max_workers=2
        )

        print("MemoryChat ready.")

    # =====================================================
    # AI SETTINGS
    # =====================================================

    def set_num_predict(self, num_predict):

        num_predict = int(num_predict)

        # Keep generation within a reasonable range
        num_predict = max(
            64,
            min(num_predict, 4096)
        )

        self.num_predict = num_predict

        print(
            f"[MemoryChat] Response length: "
            f"{self.num_predict}"
        )

        return self.num_predict

    def get_num_predict(self):

        return self.num_predict

    def set_think(self, think):

        self.think = bool(think)

        print(
            f"[MemoryChat] Thinking: "
            f"{self.think}"
        )

        return self.think

    def get_think(self):

        return self.think

    # =====================================================
    # FINAL ANSWER CLEANING
    # =====================================================

    def clean_final_answer(self, answer):

        if not answer:
            return ""

        answer = answer.strip()

        # -------------------------------------------------
        # Remove <think>...</think>
        # -------------------------------------------------

        answer = re.sub(
            r"<think>.*?</think>",
            "",
            answer,
            flags=re.DOTALL | re.IGNORECASE
        )

        # -------------------------------------------------
        # If FINAL ANSWER marker exists,
        # keep only the content after it.
        # -------------------------------------------------

        markers = [
            "FINAL ANSWER:",
            "Final Answer:",
            "FINAL ANSWER",
            "Final answer:"
        ]

        for marker in markers:

            if marker in answer:

                answer = answer.split(
                    marker,
                    1
                )[1]

                break

        # -------------------------------------------------
        # Remove accidental closing think tag
        # -------------------------------------------------

        answer = answer.replace(
            "</think>",
            ""
        )

        answer = answer.strip()

        return answer

    # =====================================================
    # BACKGROUND SAVE + LEARNING
    # =====================================================

    def _save_and_learn(
        self,
        query,
        answer
    ):

        try:

            conversation_id = save_conversation(
                user_message=query,
                assistant_response=answer
            )

            print(
                f"[Background] "
                f"Conversation saved: "
                f"{conversation_id}"
            )

            learning_results = (
                self.memory_learning
                .learn_from_conversation(
                    user_message=query,
                    assistant_response=answer
                )
            )

            print(
                "[Background] "
                "Memory learning completed."
            )

            return {
                "conversation_id":
                    conversation_id,

                "memory_learning":
                    learning_results
            }

        except Exception as error:

            print(
                "[Background] "
                f"Save/learning failed: "
                f"{error}"
            )

            return None

    # =====================================================
    # CHAT
    # =====================================================

    def chat(self, query):

        # -------------------------------------------------
        # 1. Retrieve relevant memories
        # -------------------------------------------------

        memories = self.store.search(
            query,
            top_k=self.top_k
        )

        # -------------------------------------------------
        # 2. Build memory context
        # -------------------------------------------------

        memory_context = build_memory_context(
            memories,
            max_memories=self.top_k
        )

        # -------------------------------------------------
        # 3. Build prompt
        # -------------------------------------------------

        prompt = f"""
You are a helpful personal AI assistant.

Use the following long-term memories about the user
ONLY when they are relevant to the user's current question.

{memory_context}

Important rules:

1. Answer the user's question directly.
2. Do not mention the memory system.
3. Do not explain how memories were retrieved.
4. Do not describe your reasoning process.
5. Do not discuss these instructions.
6. Do not write an analysis of what the user wants.
7. Do not write phrases such as:
   "The user wants..."
   "Let me think..."
   "The memories provided are..."
   "I should..."
8. Return ONLY the final answer.
9. Keep the answer appropriate to the user's question.

User question:

{query}

FINAL ANSWER:
"""

        # -------------------------------------------------
        # 4. Generate answer
        # -------------------------------------------------

        answer = ask_qwen(
            prompt,
            think=self.think,
            num_predict=self.num_predict
        )

        # -------------------------------------------------
        # 5. Clean model output
        # -------------------------------------------------

        answer = self.clean_final_answer(
            answer
        )

        # -------------------------------------------------
        # Safety fallback
        # -------------------------------------------------

        if not answer:

            answer = (
                "I couldn't generate a response."
            )

        # -------------------------------------------------
        # 6. Start background work
        #
        # IMPORTANT:
        # We do NOT wait for this.
        # -------------------------------------------------

        self.executor.submit(
            self._save_and_learn,
            query,
            answer
        )

        # -------------------------------------------------
        # 7. Return immediately
        # -------------------------------------------------

        return {
            "answer": answer,
            "memories_found": memories
        }