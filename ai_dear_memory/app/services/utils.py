import asyncio
from app.core.config import genai, index


def remove_dear_memory_prefix(text: str) -> str:
    """
    Removes variations of "Dear Memory"
    from the beginning of the given text.

    Args:
        text (str): The input text.

    Returns:
        str: The text with the prefix removed, if present.
    """
    if text.lower().startswith(("dear memory")):
        text = text[len("Dear Memory") :].strip()

    return text


async def fetch_vectors(user_id, vector_ids):
    """
    Fetch vectors from the index filtered by user_id.

    Args:
        user_id (int): The user ID to filter by.
        vector_ids (list): A list of vector IDs to fetch.

    Returns:
        dict: A dictionary of vectors (vector_id: vector_data) that match the user_id.
    """

    response = await asyncio.to_thread(index.fetch, ids=vector_ids)

    user_vectors = {
        vector_id: vector_data
        for vector_id, vector_data in response.vectors.items()
        if vector_data["metadata"]["userId"] == user_id
    }

    return user_vectors


async def get_text_embedding(
    text: str | list[str], model: str = "models/gemini-embedding-exp-03-07"
) -> list[float] | list[list[float]] | None:
    """
    Generates vector embeddings for given text(s) using the specified Gemini model.

    Args:
        text (str | list[str]): A single string or list of strings to embed.
        model (str): The embedding model to use.

    Returns:
        Embedding(s) as list[float] or list[list[float]], matching input type.
    """
    try:
        if not isinstance(text, (str, list)):
            raise ValueError("Input must be a string or a list of strings.")

        response = await asyncio.to_thread(genai.embed_content, model, text)
        return response.get("embedding", [])

    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None
