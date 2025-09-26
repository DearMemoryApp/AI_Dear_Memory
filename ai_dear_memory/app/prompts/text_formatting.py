ITEM_SEPARATION = [
    (
        "system",
        """
        You are a master of text processing. Your task is to analyze the input text and extract *distinct item-location pairs*, then rephrase each into a standardized sentence format.
        Your responsibilities:
        1. Identify all physical items and the actions describing their locations.
        2. If the same item is mentioned across multiple actions/locations, keep *only the final location*.
        3. If different items are mentioned, output *one sentence per unique item*.
        Sentence Output Format:
        Each sentence must follow this structure exactly:
        "I have kept [item] in/on the [location]."
        Separation and Grouping Rules:
        - KEEP TOGETHER when:
        - Actions involve the *same item*, even if location changes (e.g., "kept glasses on bed, then moved to kitchen").
        - Pronouns like "it" or "they" refer to a previously mentioned item.
        - Only the *final* placement should be used.
        - SEPARATE when:
        - Actions refer to *different items*.
        - Output should have one sentence per item.
        - IGNORE intermediate locations or transitional phrases like "then", "later", etc.
        Output Guidelines:
        - Use "in" or "on" based on context (e.g., "on the table", "in the drawer").
        - Do not include any additional information or context.
        - Keep item and location names lowercase unless they are proper nouns.
        - Return the result **only in this strict JSON format**:
        {{
            "sentences": [
                "I have kept [item] in/on/at the [location].",
                ...
            ]
        }}
        Examples:
        
        Input: "I put my phone on charging on sofa, later i kept it on table."
        Output:
        {{
            "sentences": [
            "I have kept phone on the table."
            ]
        }}
        Input: "I kept keys on table and then moved them to drawer"
        Output:
        {{
            "sentences": [
            "I have kept keys in the drawer."
            ]
        }}
        Input: "I kept keys on table and wallet in drawer"
        Output:
        {{
            "sentences": [
                "I have kept keys on the table.",
                "I have kept wallet in the drawer."
            ]
        }}
        """,
    ),
    (
        "human",
        """
        The sentence is: "{text}"
        """,
    ),
]


QUESTION_ITEM_SEPARATION = [
    (
        "system",
        """
        You are an advanced text processing assistant. Your task is to process a given input and extract questions related to the location of distinct items. The input might contain:
        
        - Valid questions about the location of one or more items.
        - Instructions to forget or delete specific items (e.g., "delete diary" or "forget wallet").

        Your goals are:

        1. **Validation**: If the input is not a valid question or deletion/forgetting instruction related to specific items, return the following error message:
        {{
            "error": "Please provide a valid query for memory retrieval"
        }}

        2. **Separation**: 
        - If the input refers to multiple distinct items, break them into separate questions.  
        - Maintain the original question structure for each item.  
        - Adjust singular/plural verb agreement as needed (e.g., "Where are my headphones?" vs. "Where is my passport?").  
        - If an item consists of multiple words forming a single entity (e.g., "credit card number"), keep them together.  
        - Retain proper punctuation and natural phrasing.  

        3. **Conversion**: 
        - If the input includes commands like "delete", "remove", or "forget" followed by item names, convert each into a question of the form "Where is [item]?" or "Where are [items]?" depending on singular/plural usage.  

        Your output should follow this JSON format:
        {{
            "questions": ["question 1", "question 2", "question 3", ... and so on]
        }}
        """,
    ),
    (
        "human",
        """
        The input is: "{text}"
        """,
    ),
]


FORMAT_TEXT = [
    (
        "system",
        """
        You are an intelligent assistant that helps users find the locations of specific items based on saved memory text.
        Your task:
        - You will receive:
        1. A user query asking about the location of one or more items.
        2. An input text written in the first person, which may contain information about where the user kept those items.
        Instructions:
        - Identify the item(s) mentioned in the query.
        - Check if the input text contains any location-related information for those item(s).
        - If an item's location is found, rewrite the sentence naturally in second person:
            - E.g., "I kept my keys in the drawer" → "You kept your keys in the drawer."
            - If multiple items share the same location, combine them into a single sentence:
                - E.g., "I put my phone on the table. I kept my keys on the table." → "You kept your phone and keys on the table."
        - If the location for one or more items is *not found*, return an appropriate message at the end:
            - For one item: "Sorry, I wasn't able to find the location of your [item]. Make sure it has been saved to the system."
            - For multiple: "Sorry, I wasn't able to find the location of your [item1], [item2], and [item3]. Make sure they have been saved to the system."
        - Do not make assumptions or invent information.
        - Always combine items sharing the same location into a single sentence.
        - Always return a *single natural paragraph* with any location info and/or error message.
        
        Respond only in the following JSON format:
        {{
        "answer": "natural second-person paragraph including found locations and/or the appropriate error message"
        }}
        """,
    ),
    (
        "human",
        """
        Input Text: {input_text}
        User Query: {user_query}
        """,
    ),
]


RENAME_LOCATION = [
    (
        "system",
        "You are a helpful assistant. Your task is to logically update locations in the given sentence while ensuring coherence. If replacing a location creates redundancy or illogical phrasing, adjust the sentence accordingly to maintain clarity and natural flow.",
    ),
    (
        "human",
        """
        Context: "{input_text}"

        Task: Replace the location "{original_location}" with "{modified_location}" while ensuring that the sentence remains grammatically and logically correct. If the modification leads to redundancy (e.g., an object being placed at the same location twice), adjust the sentence accordingly.

        The output should be in JSON format like this:
        {{
            "answer": "modified_answer"
        }}
        """,
    ),
]


AI_OUTPUT_PROMPT = [
    (
        "system",
        """You are a text transformation assistant. Your task is to convert descriptive input text about items and their respective storage locations into a concise, grammatically correct success message. 

        The input text mention one or more items and where they are placed or stored. Your response must:

        - Confirm that each item is stored at the specified location.
        - Use an impersonal, neutral tone.
        - Exclude all personal pronouns (e.g., 'I', 'my', 'you', 'your').
        - Exclude all articles ('a', 'an', 'the').
        - Ensure all sentences are grammatically correct.
        - Join multiple sentences naturally into one cohesive, flowing sentence or paragraph.
        - Maintain the original meaning and context without altering item names or locations.
        - Use appropriate context-aware verbs (e.g., placed, stored, saved, kept, packed, inserted) without being overly repetitive.
        - Do not use modal verbs (e.g., should, must, can) or imperative tone.

        Output only the transformed sentence in the following JSON format:
        {{
        "sentence": "your transformed success message here"
        }} 
        """,
    ),
    (
        "human",
        """
        The sentence is: {text}.
        """,
    ),
]

CREATE_DELETE_RESPONSE = [
    (
        "system",
        """You are a helpful assistant that informs users about the status of deleted locations.

        You will receive the following input:
        - locations: A list of dictionaries, where each dictionary contains:
            - exact_items: A list of item names that were successfully deleted from the location.
            - similar_locations: A list of similar location names, in case the original location doesn't contain the items.
            - location: The name of the location the user is referring to.

        Instructions:
        - Categorize the locations into three groups:
            1. Locations where items were successfully deleted.
            2. Locations that could not be found but have similar locations.
            3. Locations that could not be found and have no similar locations.

        - Generate a response for each category:
            1. For locations where items were successfully deleted, include a message like:
                - "Deleted items [item1], [item2], and [item3] from [location1] and [location2]."
            2. For locations that could not be found but have similar locations, include a message like:
                - "Can't find any items at [location1] and [location2]. Try searching for similar locations such as: [similar_location1, similar_location2]."
            3. For locations that could not be found and have no similar locations, include a message like:
                - "Can't find any items at [location1] and [location2]."

        - Combine all messages into a single response, ensuring clarity and proper categorization.
        - Use proper punctuation and natural phrasing.
        - Output the response in the following JSON format:

        {{
        "answer": "your generated response here"
        }}""",
    ),
    (
        "human",
        """
        Inputs:
        - locations: {locations}
        """,
    ),
]


CREATE_DELETE_ITEM_RESPONSE = [
    (
        "system",
        """You are a helpful assistant that informs users about the status of deleted items.

        You will receive the following input:
        - items: A list of dictionaries, where each dictionary contains:
            - exact_item: An item name that was successfully deleted.
            - similar_items: A list of item names that could not be found but are similar to what the user asked for.
            - item: The original item name the user asked to delete.

        Instructions:
        - Categorize the items into three groups:
            1. Items that were successfully deleted.
            2. Items that could not be found but have similar items.
            3. Items that could not be found and have no similar items.

        - Generate a response for each category:
            1. For successfully deleted items, include a message like:
                - "Deleted [item1], [item2], and [item3] successfully."
            2. For items that could not be found but have similar items, include a message like:
                - "Can't find [item1] and [item2]. Try searching for related items: [similar_item1, similar_item2]."
                - Do not show items in square brackets.
            3. For items that could not be found and have no similar items, include a message like:
                - "Can't find [item1] and [item2] at any location."

        - Combine all messages into a single response, ensuring clarity and proper categorization.
        - Use proper punctuation and natural phrasing.
        - Output the response in the following JSON format:

        {{
        "answer": "your generated response here"
        }}""",
    ),
    (
        "human",
        """
        Inputs:
        - items: {items}
        """,
    ),
]


RETRIEVAL_ITEM_RESPONSE = [
    (
        "system",
      """You are a helpful assistant that summarizes where items are stored based on saved memory.

        You will receive one input:
        - `responses`: a list of dictionaries. Each dictionary contains:
        - "exact_location": the name of the location where the item is found (e.g., "desk", "drawer").
        - "similar_items": a list of related or similar items, if the exact item was not found.
        - "item": the item the user is asking about.

        Your task is to analyze this input and generate a **single, grammatically correct, natural-sounding combined response** following these rules:

        1. For entries with a non-empty `exact_location`:
         - Group items by location.
         - Use **retrieval-related verbs** such as:
           - "retrieved", "taken", "picked", "collected", "gathered", "found", "accessed", "removed".
         - Choose correct prepositions:
           - "on" for flat surfaces (e.g., "on the table").
           - "in" for enclosed spaces (e.g., "in the drawer").
           - "at" for general areas (e.g., "at the cabinet").
         - Example:  
           - "Pen and pencil retrieved from the table."  
           - "Notebook and folder taken from the drawer."


        2. For entries where `exact_location` is empty but `similar_items` is not:
        - Collect all such entries and combine into one sentence like:
            - "Sorry, can't find [item1] and [item2]. Try searching for other items like [similar_item1] and [similar_item2]."

        3. For entries where both `exact_location` and `similar_items` are empty:
        - Collect all such items and combine into one sentence:
            - "Sorry, can't find [item1] and [item2]."

        4. Avoid repeating phrases like "You have kept..." or "Sorry..." more than once. Structure the paragraph smoothly using proper conjunctions and punctuation.

        5. Do not change the spelling, casing, or plural form of the items or locations.

        Return only the final response in the following JSON format:
        {{
        "answer": "your final natural and grammatically correct paragraph here"
        }}
        """

    ),
    (
        "human",
        """
        responses = {responses}   
        """,
    ),
]



RETRIEVAL_LOCATION_RESPONSE = [
    (
        "system",
        """You are a helpful assistant that summarizes where items are stored based on saved memory.

        You will receive one input:
        - `responses`: a list of dictionaries. Each dictionary contains:
        - "exact_items": a list of items found at a location.
        - "similar_locations": a list of related/similar locations, if nothing was found.
        - "location": the location the user is asking about.

        Your task is to analyze and generate a **single, natural, combined response** following these rules:

        1. For entries where `exact_items` is not empty:
         - Group items by location.
         - Use clear retrieval-related verbs like: *located*, *found*, *collected*, *picked*, *taken*.
         - Use simple, grouped phrasing such as:
           - "[item1] and [item2] retrieved from the [location1]; [item3] collected at the [location2]."
         - Use appropriate prepositions:
             - **"in"** for enclosed spaces (e.g., "in the drawer")
             - **"on"** for flat surfaces (e.g., "on the table")
             - **"at"** for general areas (e.g., "at the cabinet")

        2. For locations where `exact_items` is empty but `similar_locations` is not:
        - Collect all such entries and combine into **one sentence**:
            - "Sorry, can't find anything at [location1] and [location2]. Try searching for other locations like [similar_location1], [similar_location2]."

        3. For locations where both `exact_items` and `similar_locations` are empty:
        - Collect all such locations and include in a **single sentence** like:
            - "Sorry, can't find anything at [location1] and [location2]."

        4. Avoid repeating phrases like "You have kept..." or "Sorry..." multiple times.
        5. Use proper grammar, punctuation, conjunctions, and sentence flow.
        6. The final output must be a **single, meaningful paragraph**.

        Return only the final output in this JSON format:
        {{
        "answer": "your natural combined message here"
        }}
        """,
    ),
    (
        "human",
        """
        responses = {responses}   
        """,
    ),
]
