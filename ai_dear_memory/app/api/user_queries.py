from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.schemas.embeddings import EmbeddingRequest, SaveMemoryResponse
from app.schemas.rename_delete_location import (
    RenameLocationRequest,
    DeleteLocationRequest,
)
from app.services.retrieving_memory import smart_retrieval
from app.services.renaming_location import update_memory
from app.services.insert_and_delete import insert_delete
from app.services.deleting_locations import delete_loc_and_items
from app.services.utils import remove_dear_memory_prefix

user_queries_router = APIRouter(prefix="", tags=["User Queries"])


@user_queries_router.post("/save", response_model=SaveMemoryResponse)
async def save_embedding(data: EmbeddingRequest):
    """
    API endpoint to save a user's memory (text) to Pinecone.

    Args:
        data (EmbeddingRequest): The request containing user_id and text.

    Returns:
        SaveMemoryResponse: A response containing the success message and items.

    Raises:
        HTTPException: If an error occurs during the save operation.
    """
    try:
        data.text = remove_dear_memory_prefix(data.text.strip())
        result = await insert_delete(data)
        return result
    except Exception as e:
        print(e)
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while saving the memory",
            },
        )


@user_queries_router.get("/retrieve")
async def retrieve_memory(
    user_id: int = Query(..., description="The unique identifier for the user"),
    text: str = Query(..., description="The text query for embedding retrieval"),
):
    """
    API endpoint to retrieve the best matching text embedding based on a given query from a user.

    Args:
        user_id (int): The unique identifier for the user.
        text (str): The text query for embedding retrieval.

    Returns:
        JSONResponse: The most relevant text embedding from the user's memory.

    Raises:
        HTTPException: If an error occurs during the retrieval process.
    """
    try:
        text = remove_dear_memory_prefix(text.strip())

        data = EmbeddingRequest(user_id=user_id, text=text)
        result = await smart_retrieval(data)
        return result
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "An unexpected error occurred while retrieving the memory",
            },
        )


@user_queries_router.put("/rename-location")
async def renaming_location(request: RenameLocationRequest):
    """
    API endpoint to rename a location in stored text embeddings.

    Args:
        request (RenameLocationRequest): The request containing user_id, vector_ids, original_location, and modified_location.

    Returns:
        JSONResponse: A response indicating the success or failure of the rename operation.

    Raises:
        HTTPException: If an error occurs during the rename operation.
    """

    try:
        response = await update_memory(
            request.user_id,
            request.vector_ids,
            request.original_location,
            request.modified_location,
        )
        return response
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "Failed to rename the location.",
            },
        )


@user_queries_router.delete("/delete")
async def delete_location_and_items(request: DeleteLocationRequest):
    """
    API endpoint to delete a location and its associated items from the user's memory.

    Args:
        user_id (int): The unique identifier for the user.
        vector_ids (list[str]): A list of vector IDs associated with the location and items to delete.

    Returns:
        JSONResponse: A response indicating the success or failure of the delete operation.

    Raises:
        HTTPException: If an error occurs during the delete operation.
    """
    try:
        response = await delete_loc_and_items(
            request.user_id,
            request.vector_ids,
        )
        return response
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "Failed to delete the location and items.",
            },
        )
