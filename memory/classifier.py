def classify_memory(content):
    """
    Simple rule-based memory classification.
    """

    text = content.lower()

    # Preferences
    preference_words = [
        "prefer",
        "like",
        "love",
        "favorite",
        "favourite",
        "want",
        "choose"
    ]

    if any(word in text for word in preference_words):
        return "preference"

    # Projects
    project_words = [
        "project",
        "application",
        "app",
        "system",
        "website",
        "building",
        "developing",
        "develop",
        "coding"
    ]

    if any(word in text for word in project_words):
        return "project"

    # Personal information
    personal_patterns = [
        "my name",
        "my age",
        "i live",
        "my hometown",
        "i work"
    ]

    if any(pattern in text for pattern in personal_patterns):
        return "personal"

    # Interests
    interest_words = [
        "interested",
        "enjoy",
        "learning",
        "learn",
        "experiment",
        "research",
        "hobby"
    ]

    if any(word in text for word in interest_words):
        return "interest"

    return "general"