import asyncio
from app.core.config import index
from fastapi.responses import JSONResponse
from app.services.utils import fetch_vectors


async def delete_loc_and_items(user_id, vector_ids):
    """
    Delete a location and its associated vectors from the index.

    Args:
        user_id (int): The unique identifier for the user.
        vector_ids (list): A list of vector IDs associated with the location and items to delete.

    Returns:
        JSONResponse: A response indicating the success or failure of the delete operation.

    Raises:
        Exception: If an error occurs during the delete operation.
    """

    try:
        user_vectors = await fetch_vectors(user_id, vector_ids)
        if not user_vectors:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "message": "No matching location found."},
            )

        await asyncio.to_thread(
            index.delete,
            ids=list(user_vectors.keys()),
        )
        return JSONResponse(
            status_code=200,
            content={"status": 200, "message": "Location deleted successfully."},
        )

    except Exception as e:
        raise e
