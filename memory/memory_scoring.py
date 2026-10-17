def calculate_importance(content, memory_type):
    """
    Calculate importance score between 0.0 and 1.0.
    """

    text = content.lower()

    # Personal information is usually important
    if memory_type == "personal":
        return 0.9

    # Preferences are useful for personalization
    if memory_type == "preference":
        return 0.8

    # Project information is useful for future tasks
    if memory_type == "project":
        return 0.8

    # Interests are moderately important
    if memory_type == "interest":
        return 0.6

    # General information
    return 0.3


def calculate_confidence(content):
    """
    Calculate confidence score between 0.0 and 1.0.
    """

    text = content.lower()

    uncertain_words = [
        "maybe",
        "might",
        "possibly",
        "probably",
        "perhaps",
        "i think",
        "i guess",
        "not sure",
        "could be"
    ]

    if any(word in text for word in uncertain_words):
        return 0.6

    return 0.9