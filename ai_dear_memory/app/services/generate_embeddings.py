import uuid
import asyncio
import datetime
from app.core.config import index
from fastapi.responses import JSONResponse
from app.schemas.embeddings import EmbeddingRequest, EmbeddingResponse
from app.services.information_extraction import extract_key_value_pairs
from app.services.chain_creation import create_chain
from app.prompts.text_formatting import ITEM_SEPARATION, AI_OUTPUT_PROMPT
from app.services.retrieving_memory import (
    query_index_item,
)
from app.services.utils import get_text_embedding


async def handling_previous_entry(user_id: int, item: str, query_vector: list) -> list:
    """
    Check if an item already exists in the database by querying it and return
    existing matches if any.

    Args:
        user_id (int): The user ID.
        item (str): The item to query.
        query_vector (list): The vector to query with.

    Returns:
        list: List of existing matches if any. Otherwise an empty list.
    """
    result = await query_index_item(user_id, item, [query_vector], top_k=3)

    if result and result[0].get("matches"):
        return result[0]["matches"]
    return []


async def process_sentence(sentence: str, user_id: int, embedding: list) -> dict | None:
    """
    Process a single sentence to extract information and handle existing entries.

    Args:
        sentence (str): Input sentence
        user_id (int): User ID
        embedding (list): Pre-generated embedding for the sentence

    Returns:
        dict: Processing results including vector ID, location, item, and deleted entries
    """
    try:
        # Use the provided embedding and check for exact matches
        if not embedding:
            raise ValueError("Embedding is missing or invalid.")
        deleted_entries = []

        try:
            extracted_info = await extract_key_value_pairs(sentence)
            if extracted_info.get("error"):
                return {
                    "error": "Sorry, I couldn't understand that sentence. Please make sure you're clearly mentioning where and what item you're referring to."
                }
        except Exception:
            return {
                "error": "Something went wrong while trying to understand your sentence. Please rephrase and try again."
            }
        if not extracted_info or not isinstance(extracted_info, dict):
            return {
                "error": "Sorry, I couldn't understand that sentence. Please make sure you're clearly mentioning where and what item you're referring to."
            }

        try:
            location, item = list(extracted_info.items())[0]
            if not location or not item:
                raise ValueError("Missing location or item")
        except Exception:
            return {
                "error": "It looks like I couldn’t extract both the 'location' and the 'item'. Please rephrase your sentence—for example, 'I kept my headphones in the drawer.'"
            }
        matches = await handling_previous_entry(user_id, item, embedding)
        if matches:
            matched_object = matches[0]
            if matched_object["metadata"]["location"] == location.lower().strip():
                return {
                    "vector_id": matched_object["id"],
                    "location": matched_object["metadata"]["location"],
                    "item": matched_object["metadata"]["item"],
                    "exists": True,
                    "originalText": matched_object["metadata"]["originalText"],
                }
            else:
                deleted_entries = [matched_object["id"]]

        # Create metadata for the new entry
        metadata = {
            "userId": user_id,
            "originalText": sentence,
            "datetime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "location": location,
            "item": item,
        }

        vector_id = str(uuid.uuid4())
        return {
            "vector_id": vector_id,
            "embedding": embedding,
            "metadata": metadata,
            "location": location,
            "item": item,
            "exists": False,
            "deleted_entries": deleted_entries,
        }

    except Exception as e:
        print(f"Error processing sentence: {e}")
        return None


async def insert_embedding(request_body: EmbeddingRequest) -> dict | JSONResponse:
    """
    Inserts data into Pinecone index after processing sentences.

    Args:
        request_body (EmbeddingRequest): Request containing user ID and text

    Returns:
        dict: Response containing processing results or error message
    """
    try:
        # Split text into sentences
        sentences_chain = await create_chain(
            ITEM_SEPARATION, {"text": request_body.text}
        )
        sentences = sentences_chain["sentences"]

        # Batch embedding generation
        embeddings = await get_text_embedding(sentences)

        # Process all sentences concurrently
        results = await asyncio.gather(
            *[
                process_sentence(sentence, request_body.user_id, embedding)
                for sentence, embedding in zip(sentences, embeddings)
                if embedding  # Skip sentences with failed embeddings
            ]
        )

        # Separate results into categories
        embedding_responses = []
        existing_sentences = []
        deleted_entries = []
        new_entries = []  # Store new entries for deferred insertion

        for result in results:
            if not result:
                continue
            if "error" in result:
                return JSONResponse(
                    status_code=400,
                    content={"status": 400, "error": result["error"]},
                )

            if result.get("exists", False):
                existing_sentences.append(result["originalText"])
            else:
                # Collect new entries for deferred insertion
                new_entries.append(
                    (
                        result["vector_id"],
                        result["embedding"],
                        result["metadata"],
                    )
                )
                embedding_responses.append(
                    EmbeddingResponse(
                        vector_id=result["vector_id"],
                        location=result["location"],
                        item=result["item"],
                    )
                )

            if result.get("deleted_entries"):
                deleted_entries.extend(result["deleted_entries"])

        # Handle existing sentences
        if existing_sentences:
            processed_output = await create_chain(
                AI_OUTPUT_PROMPT, {"text": " ".join(existing_sentences)}
            )
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": f"Similar memory already exists: '{processed_output.get('sentence', ' '.join(existing_sentences))}'. Please try again with a different sentence.",
                },
            )

        if deleted_entries:
            await asyncio.to_thread(index.delete, ids=deleted_entries)

        if new_entries:
            await asyncio.to_thread(index.upsert, vectors=new_entries)

        # Handle successful insertion
        if embedding_responses:
            processed_output = await create_chain(
                AI_OUTPUT_PROMPT, {"text": request_body.text}
            )
            return {
                "user_id": request_body.user_id,
                "success_message": processed_output.get("sentence", request_body.text),
                "deleted_entries": deleted_entries,
                "items": embedding_responses,
            }

        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "error": "Sorry, I couldn't understand that sentence. Please make sure you're clearly mentioning where and what item you're referring to.",
            },
        )

    except Exception as e:
        print(f"Error inserting data: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while saving the memory.",
            },
        )
