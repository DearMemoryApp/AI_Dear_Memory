from app.schemas.embeddings import EmbeddingRequest
import google.generativeai as genai
from google.generativeai import types
from app.services.generate_embeddings import insert_embedding
from app.services.retrieving_memory import (
    query_index,
    extract_valid_matches,
    sort_by_score,
)
import asyncio
from fastapi.responses import JSONResponse
from app.services.utils import get_text_embedding
from app.core.config import index
from app.services.chain_creation import create_chain
from app.prompts.text_formatting import FORMAT_TEXT
from app.prompts.text_formatting import (
    CREATE_DELETE_RESPONSE,
    CREATE_DELETE_ITEM_RESPONSE,
)
from typing import Dict, Any


insert_memory_declaration = {
    "name": "insert_embedding",
    "description": "Extract the item and its location from a natural language sentence and insert it into the database or system.",
    "parameters": {
        "type": "object",
        "properties": {
            "item": {
                "type": "string",
                "description": "The object or item being placed or stored. Extract this from the sentence.",
            },
            "location": {
                "type": "string",
                "description": "The location or place where the item has been stored. Extract this from the sentence.",
            },
        },
        "required": ["item", "location"],
    },
}

delete_memory_item_declaration = {
    "name": "delete_memory_item",
    "description": (
        "Deletes all the item(s) exactly as specified by the user. "
        "Do not correct or change the spelling, pluralization, or casing of any item name. "
        "For example, if the user says 'delete chareger', you must include 'chareger' as-is in the items list."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": (
                    "The name(s) of the item(s) to be deleted. "
                    "Preserve the original spelling, pluralization, and casing exactly as in the user input. "
                    "Examples: 'chareger', 'keys', 'NoteBook'."
                ),
                "items": {"type": "string"},
            },
        },
        "required": ["items"],
    },
}

delete_memory_location_declaration = {
    "name": "delete_memory_location",
    "description": (
        "Deletes all the items at the specified location(s) exactly as provided by the user. "
        "Do not correct or change the spelling, pluralization, or casing of any location name. "
        "For example, if the user says 'delete from drower', you must include 'drower' as-is in the locations list."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "locations": {
                "type": "array",
                "description": (
                    "The name(s) of the location(s) whose items are to be deleted. "
                    "Preserve the original spelling, pluralization, and casing exactly as in the user input. "
                    "Examples: 'drower', 'tables', 'StudyRoom'."
                ),
                "items": {"type": "string"},
            },
        },
        "required": ["locations"],
    },
}


async def query_index_location(
    user_id: int, vectors: list, location: str, top_k: int
) -> list:
    return await asyncio.gather(
        *[
            asyncio.to_thread(
                index.query,
                vector=vec,
                top_k=top_k,
                filter={"userId": user_id, "location": location.lower().strip()},
                include_metadata=True,
            )
            for vec in vectors
        ]
    )


async def query_index_item(user_id: int, item: str, vectors: list, top_k: int) -> list:
    return await asyncio.gather(
        *[
            asyncio.to_thread(
                index.query,
                vector=vec,
                top_k=top_k,
                filter={"userId": user_id, "item": item.lower().strip()},
                include_metadata=True,
            )
            for vec in vectors
        ]
    )


async def prepare_response(input_text: str, user_query: str) -> Dict[str, Any]:
    try:
        return await create_chain(
            FORMAT_TEXT, {"input_text": input_text, "user_query": user_query}
        )
    except Exception as e:
        print(f"An error occurred while formatting response: {e}")
        return {}


async def process_items_in_batch(user_id: int, items: list[str], top_k: int = 3):
    """
    Process multiple items for deletion in a batch.

    Args:
        user_id (int): The user ID.
        items (list[str]): List of items to process.
        top_k (int): Number of top matches to retrieve.

    Returns:
        list[dict]: A list of dictionaries containing results for each item.
    """
    questions = [f"Where is {item}?" for item in items]
    query_vectors = await asyncio.gather(*(get_text_embedding(q) for q in questions))
    query_results = await asyncio.gather(
        *[
            query_index_item(user_id, item, [vec], top_k)
            for item, vec in zip(items, query_vectors)
        ]
    )

    results = []
    for item, query_result in zip(items, query_results):
        if query_result[0]["matches"]:
            result = query_result[0]["matches"][0]
            await asyncio.to_thread(index.delete, ids=[result["id"]])
            results.append(
                {
                    "exact_item": result["metadata"]["item"],
                    "similar_items": [],
                    "deleted_id": result["id"],
                }
            )
        else:
            # Handle similar items in batch
            similar_query_results = await query_index(user_id, query_vectors, top_k)
            similar_items = set()
            for res in similar_query_results:
                matches = extract_valid_matches(res["matches"], 0.65)
                matches = sort_by_score(matches)
                similar_items.update([m["metadata"]["item"] for m in matches])
            results.append(
                {
                    "exact_item": "",
                    "similar_items": similar_items,
                    "deleted_id": None,
                }
            )
    return results


async def delete_memory_item(user_id: int, items: list[str]):
    """
    Delete memory items for a user.

    Args:
        user_id (int): The user ID.
        items (list[str]): List of items to delete.

    Returns:
        dict: A dictionary containing the success message, deleted entries, and items, or a 404 response if no items are found.
    """
    try:
        if not items:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, not able to understand the query, please try again.",
                },
            )

        # Process items in batch
        results = await process_items_in_batch(user_id, items)

        # Prepare input for the prompt
        prompt_input = []
        deleted_entries = []
        any_item_deleted = False

        for result, item in zip(results, items):
            prompt_input.append(
                {
                    "exact_item": result["exact_item"],
                    "similar_items": list(result["similar_items"]),
                    "item": item.lower().strip(),
                }
            )
            if result["deleted_id"]:
                any_item_deleted = True
                deleted_entries.append(result["deleted_id"])

        # Generate a single response for all items
        response = await create_chain(
            CREATE_DELETE_ITEM_RESPONSE, {"items": prompt_input}
        )

        if not any_item_deleted:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "error": response["answer"],
                },
            )

        return {
            "user_id": user_id,
            "success_message": response["answer"],
            "deleted_entries": deleted_entries,
            "items": [],
        }

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while retrieving the memory.",
            },
        )


async def process_location(user_id: int, location: str):
    """
    Process a single location for deletion.

    Args:
        user_id (int): The user ID.
        location (str): The location to process.

    Returns:
        dict: A dictionary containing exact items, similar locations, and deleted entries.
    """
    question = f"What did I keep at {location}?"
    query_vector = await get_text_embedding(question)
    query_result = await query_index_location(
        user_id, [query_vector], location, top_k=100
    )
    exact_items = []
    similar_locations = set()
    deleted_entries = []

    if query_result[0]["matches"] != []:
        results = query_result[0]["matches"]
        for result in results:
            await asyncio.to_thread(index.delete, ids=[result.id])
            deleted_entries.append(result.id)
            exact_items.append(result["metadata"]["item"])
    else:
        query_result_similar = await query_index(user_id, [query_vector], top_k=3)
        matches = extract_valid_matches(query_result_similar[0]["matches"], 0.75)
        if matches:
            for match in matches:
                similar_locations.add(match["metadata"]["location"])

    return {
        "exact_items": exact_items,
        "similar_locations": similar_locations,
        "deleted_entries": deleted_entries,
        "location": location,
    }


async def delete_memory_location(user_id: int, locations: list[str]):
    """
    Delete memory locations for a user.

    Args:
        user_id (int): The user ID.
        locations (list[str]): List of locations to delete.

    Returns:
        dict: A dictionary containing the success message, deleted entries, and items.
    """
    try:
        if not locations:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, not able to understand the query, please try again.",
                },
            )

        # Process all locations concurrently
        results = await asyncio.gather(
            *(process_location(user_id, location) for location in locations)
        )

        # Prepare input for the prompt
        prompt_input = []
        deleted_entries = []
        any_location_deleted = False

        for result, location in zip(results, locations):
            prompt_input.append(
                {
                    "exact_items": result["exact_items"],
                    "similar_locations": list(result["similar_locations"]),
                    "location": location,
                }
            )
            if result["deleted_entries"]:
                any_location_deleted = True
                deleted_entries.extend(result["deleted_entries"])

        # Generate a single response for all locations
        response = await create_chain(
            CREATE_DELETE_RESPONSE, {"locations": prompt_input}
        )

        if not any_location_deleted:
            return JSONResponse(
                status_code=404,
                content={
                    "status": 404,
                    "error": response["answer"],
                },
            )

        return {
            "user_id": user_id,
            "success_message": response["answer"],
            "deleted_entries": deleted_entries,
            "items": [],
        }

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while processing the statement. Please try again.",
            },
        )


async def insert_delete(data: EmbeddingRequest):
    try:
        tools = types.Tool(
            function_declarations=[
                insert_memory_declaration,
                delete_memory_item_declaration,
                delete_memory_location_declaration,
            ]
        )
        model = genai.GenerativeModel("models/gemini-2.0-flash", tools=[tools])

        response = await asyncio.to_thread(model.generate_content, data.text)

        function_call = response.candidates[0].content.parts[0].function_call

        if function_call.name == "insert_embedding":
            return await insert_embedding(data)
        elif function_call.name == "delete_memory_item":
            return await delete_memory_item(data.user_id, **function_call.args)
        elif function_call.name == "delete_memory_location":
            return await delete_memory_location(data.user_id, **function_call.args)
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, not able to understand the statement. Please try again.",
                },
            )

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while processing the statement. Please try again.",
            },
        )
