def build_memory_context(
    memories,
    max_memories=5,
    include_scores=False
):
    """
    Convert retrieved memories into compact,
    deduplicated text context.
    """

    if not memories:
        return "No relevant memories found."

    lines = ["Relevant memories:"]
    seen_content = set()

    count = 0

    for memory in memories:

        content = memory["content"].strip()

        # Skip duplicate content
        if content in seen_content:
            continue

        seen_content.add(content)

        line = (
            f"- {content} "
            f"(type: {memory['memory_type']})"
        )

        if include_scores:
            line += (
                f" [importance: {memory['importance']:.2f},"
                f" confidence: {memory['confidence']:.2f},"
                f" relevance: {memory['final_score']:.2f}]"
            )

        lines.append(line)

        count += 1

        if count >= max_memories:
            break

    return "\n".join(lines)