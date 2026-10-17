import re


def extract_memories(user_message, assistant_response=None):
    """
    Extract explicit long-term user information using rules.

    Qwen is not used here.
    assistant_response is kept in the function signature for compatibility.
    """

    text = user_message.strip()
    memories = []

    # ---------------------------------------------------------
    # Preferences
    # ---------------------------------------------------------

    preference_patterns = [
        r"\bI prefer ([^.?!]+)",
        r"\bI like ([^.?!]+)",
        r"\bI love ([^.?!]+)",
        r"\bI favor ([^.?!]+)",
        r"\bI use ([^.?!]+)",
        r"\bI want to use ([^.?!]+)",
    ]

    for pattern in preference_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            sentence = match.strip()

            if sentence:
                memories.append(
                    f"I prefer {sentence}."
                )

    # ---------------------------------------------------------
    # Projects / things currently being built
    # ---------------------------------------------------------

    # Projects / things currently being built
    project_patterns = [
        r"\bI'm currently building ([^.?!]+)",
        r"\bI am currently building ([^.?!]+)",
        r"\bI'm building ([^.?!]+)",
        r"\bI am building ([^.?!]+)",
        r"\bI'm developing ([^.?!]+)",
        r"\bI am developing ([^.?!]+)",
        r"\bI'm working on ([^.?!]+)",
        r"\bI am working on ([^.?!]+)",
    ]

    for pattern in project_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            project = match.strip()

            if project:
                memories.append(f"I am building {project}.")

    # ---------------------------------------------------------
    # Interests
    # ---------------------------------------------------------

    interest_patterns = [
        r"\bI'm interested in ([^.?!]+)",
        r"\bI am interested in ([^.?!]+)",
        r"\bI enjoy ([^.?!]+)",
        r"\bI like learning ([^.?!]+)",
        r"\bI'm learning ([^.?!]+)",
        r"\bI am learning ([^.?!]+)",
    ]

    for pattern in interest_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            interest = match.strip()

            if interest:
                memories.append(
                    f"I am interested in {interest}."
                )

    # ---------------------------------------------------------
    # Goals
    # ---------------------------------------------------------

    goal_patterns = [
        r"\bI want to learn ([^.?!]+)",
        r"\bI want to build ([^.?!]+)",
        r"\bI plan to ([^.?!]+)",
        r"\bI'm planning to ([^.?!]+)",
        r"\bI am planning to ([^.?!]+)",
    ]

    for pattern in goal_patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)

        for match in matches:
            goal = match.strip()

            if goal:
                memories.append(
                    f"I want to {goal}."
                )

    # ---------------------------------------------------------
    # Remove duplicates
    # ---------------------------------------------------------

    unique_memories = []
    seen = set()

    for memory in memories:
        normalized = memory.lower().strip()

        if normalized not in seen:
            seen.add(normalized)
            unique_memories.append(memory)

    return unique_memories