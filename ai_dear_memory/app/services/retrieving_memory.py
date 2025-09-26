import asyncio
from typing import Dict, Any
from app.core.config import index
import google.generativeai as genai
from google.generativeai import types
from fastapi.responses import JSONResponse
from app.schemas.embeddings import EmbeddingRequest
from app.services.utils import get_text_embedding
from app.services.chain_creation import create_chain
from app.prompts.text_formatting import (
    FORMAT_TEXT,
    RETRIEVAL_LOCATION_RESPONSE,
    RETRIEVAL_ITEM_RESPONSE,
)


RETRIEVAL_LOC_BASED_DEC = {
    "name": "retrieving_memory_by_location",
    "description": (
        "Retrieve all the item(s) that are stored in specific locations, containers, or places. "
        "This includes bags, rooms, boxes, or any other storage location. "
        "Only call this function when the user is explicitly asking about what items are stored in a location. "
        "Do NOT call this function if the user is simply making a statement or describing where items are."
        "Preserve the original spelling, pluralization, and casing of all item names exactly as given by the user. "
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "locations": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "A location, container, or place to retrieve items from (e.g., 'travel bag', 'kitchen drawer', 'bedroom closet').",
                },
                "description": "The locations, containers, or places to retrieve items from."
                "All names must be kept exactly as the user typed them.",
            }
        },
        "required": ["locations"],
    },
}


RETRIEVAL_ITEM_BASED_DEC = {
    "name": "retrieving_memory_by_item",
    "description": (
        "Retrieve information about specific item(s) the user is asking about, including their locations and any related details. "
        "Only call this function when the user is explicitly asking about an item's location or related information. "
        "Do NOT call this function if the user is simply stating where something is or mentioning a past action. "
        "Preserve the original spelling, pluralization, and casing of all item names exactly as given by the user. "
        "For example, if the user types 'chareger' or 'Keys', retain them as-is without correction or modification."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": (
                        "The name of an item to retrieve information for. "
                        "Do NOT modify the original spelling, casing, or pluralization."
                    ),
                },
                "description": (
                    "A list of item names whose location and detail information needs to be retrieved. "
                    "All names must be kept exactly as the user typed them."
                ),
            }
        },
        "required": ["items"],
    },
}


async def query_index(user_id: str, vectors: list, top_k: int) -> list:
    return await asyncio.gather(
        *[
            asyncio.to_thread(
                index.query,
                vector=vec,
                top_k=top_k,
                filter={"userId": user_id},
                include_metadata=True,
            )
            for vec in vectors
        ]
    )


def extract_valid_matches(matches, min_score: float) -> list:
    return (
        [match for match in matches if match["score"] >= min_score] if matches else []
    )


def sort_by_score(matches):
    return sorted(
        matches,
        key=lambda x: (x["score"]),
        reverse=True,
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


async def query_index_location(
    user_id: str, location: str, vectors: list, top_k: int
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


async def process_item(data: EmbeddingRequest, item: str, min_score: float):
    question = f"Where is {item}"
    query_vector = await get_text_embedding(question)

    query_result = await query_index_item(data.user_id, item, [query_vector], top_k=3)

    result = set()
    similar_items = set()

    if query_result and query_result[0]["matches"]:
        top_match = query_result[0]["matches"][0]
        result.add(top_match["metadata"]["location"])
        return {
            "exact_location": result,
            "similar_items": similar_items,
            "item": item,
            "status_code": 200,
        }

    else:
        query_result = await query_index(data.user_id, [query_vector], top_k=3)
        matches = extract_valid_matches(query_result[0]["matches"], min_score)
        matches = sort_by_score(matches)

        if matches:
            for match in matches:
                similar_items.add(match["metadata"]["item"])
        return {
            "exact_location": result,
            "similar_items": similar_items,
            "item": item,
            "status_code": 404,
        }


async def process_location(data: EmbeddingRequest, location: str, min_score=0.70):
    question = f"What did I keep in {location}?"
    query_vector = await get_text_embedding(question)

    query_result = await query_index_location(
        data.user_id, location, [query_vector], top_k=100
    )

    result = set()
    similar_locations = set()
    if query_result and query_result[0]["matches"]:
        for match in query_result[0]["matches"]:
            result.add(match["metadata"]["item"])
        return {
            "exact_items": result,
            "similar_locations": similar_locations,
            "location": location,
            "status_code": 200,
        }
    else:
        query_result = await query_index(data.user_id, [query_vector], top_k=3)
        matches = extract_valid_matches(query_result[0]["matches"], 0.70)
        matches = sort_by_score(matches)

        if matches:
            for match in matches:
                similar_locations.add(match["metadata"]["location"])
        return {
            "exact_items": result,
            "similar_locations": similar_locations,
            "location": location,
            "status_code": 404,
        }


async def retrieving_memory_by_item(
    data: EmbeddingRequest, items: list[str], min_score=0.65
):
    """
    Retrieve information about specific items the user is asking about.

    Args:
        data (EmbeddingRequest): The request containing user_id and text.
        items (list[str]): List of items to retrieve information for.
        min_score (float): Minimum score threshold for valid matches.

    Returns:
        JSONResponse: The response containing the retrieved memory or an error message.
    """
    try:
        if not items:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, I am not able to understand the item you are asking for. Please try again.",
                },
            )

        # Process each item asynchronously
        responses = await asyncio.gather(
            *(process_item(data, item, min_score) for item in items)
        )

        result = await create_chain(RETRIEVAL_ITEM_RESPONSE, {"responses": responses})

        any_success = False

        for response in responses:
            if response["status_code"] == 200:
                any_success = True
                break

        status_code = 200 if any_success else 404

        result["status"] = status_code

        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while retrieving the memory.",
            },
        )


async def retrieving_memory_by_location(
    data: EmbeddingRequest, locations: list[str], min_score=0.75
):
    try:
        if not locations:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, I am not able to understand the location you are asking for. Please try again.",
                },
            )
        # Process each location asynchronously
        responses = await asyncio.gather(
            *(process_location(data, location, min_score) for location in locations)
        )

        any_success = False

        for response in responses:
            if response["status_code"] == 200:
                any_success = True
                break

        status_code = 200 if any_success else 404

        result = await create_chain(
            RETRIEVAL_LOCATION_RESPONSE, {"responses": responses}
        )

        result["status"] = status_code

        return JSONResponse(status_code=status_code, content=result)

    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while retrieving the memory",
            },
        )


async def prepare_response(input_text: str, user_query: str) -> Dict[str, Any]:
    try:
        return await create_chain(
            FORMAT_TEXT, {"input_text": input_text, "user_query": user_query}
        )
    except Exception as e:
        print(f"An error occurred while formatting response: {e}")
        return {}


async def smart_retrieval(request_body: EmbeddingRequest) -> Dict[str, Any]:
    try:
        tools = types.Tool(
            function_declarations=[RETRIEVAL_LOC_BASED_DEC, RETRIEVAL_ITEM_BASED_DEC]
        )
        model = genai.GenerativeModel("models/gemini-1.5-pro", tools=[tools])

        response = await asyncio.to_thread(model.generate_content, request_body.text)

        parts = response.candidates[0].content.parts if response.candidates else []
        if not parts or not parts[0].function_call:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, I am not able to process the query. Please rephrase and try again.",
                },
            )

        function_call = parts[0].function_call

        if function_call.name == "retrieving_memory_by_location":
            return await retrieving_memory_by_location(
                request_body, **function_call.args
            )
        elif function_call.name == "retrieving_memory_by_item":
            return await retrieving_memory_by_item(request_body, **function_call.args)
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "error": "Sorry, I am not able to process the query. Please rephrase and try again.",
                },
            )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while retrieving the memory.",
            },
        )
