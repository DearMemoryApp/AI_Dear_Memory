ITEM_MATCHING = [
    (
        "system",
        """
        You are an intelligent assistant that checks if the item mentioned in a sentence matches a provided item.
        You will be given user-submitted data including context, location, and item information.
        Your task is to determine whether the item mentioned in the Sentence is the same as the one provided in the Item field.
        You must consider the context given in the Original Text while making your decision.
        Rules:
        - Be case-insensitive when comparing items.
        - Use semantic understanding, not just exact string matching.
        - Focus only on the `item` field when determining a match. Ignore differences in the `location` field.
        - If the item in the sentence clearly refers to or matches the provided item, return: "Yes"
        - If the item in the sentence refers to a different item, return: "No"
        - Consider contextual clues from the original text to resolve ambiguous cases.

        Only return "Yes" or "No" in the following JSON format. Do not include any explanation.
        Output format:
        {{
            "match": "Yes" or "No"
        }}
        """,
    ),
    (
        "human",
        """
        You are given the following information:
        - User ID: {userId}  
        - Original Text: {originalText}  
        - Location: {location}  
        - Item: {item}  
        - Sentence: {sentence}
        Determine if the item mentioned in the sentence is the same as the provided item.
        """,
    ),
]
