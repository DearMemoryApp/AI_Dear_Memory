import asyncio
from app.core.config import index
from fastapi.responses import JSONResponse
from app.services.utils import fetch_vectors
from app.services.chain_creation import create_chain
from app.prompts.text_formatting import RENAME_LOCATION


async def rename_texts(vectors, original_location, modified_location):
    """Rename location in parallel for all vectors."""
    rename_tasks = [
        asyncio.create_task(
            create_chain(
                RENAME_LOCATION,
                {
                    "input_text": vector_data["metadata"]["originalText"],
                    "original_location": original_location,
                    "modified_location": modified_location,
                },
            )
        )
        for vector_data in vectors.values()
    ]

    updated_texts = await asyncio.gather(*rename_tasks)

    # Update metadata with new text
    for (vector_id, vector_data), updated_text in zip(vectors.items(), updated_texts):
        vector_data["metadata"]["originalText"] = updated_text["answer"]
        vector_data["metadata"]["location"] = modified_location

    return vectors


async def update_memory(user_id, vector_ids, original_location, modified_location):
    """Fetch vectors, rename locations, and update index."""
    try:
        user_vectors = await fetch_vectors(user_id, vector_ids)

        if not user_vectors:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "message": "No memories found."},
            )

        updated_vectors = await rename_texts(
            user_vectors, original_location, modified_location
        )

        # Convert to upsert format
        upsert_data = [
            (vector_id, vector_data["values"], vector_data["metadata"])
            for vector_id, vector_data in updated_vectors.items()
        ]

        # Perform a single batch upsert
        await asyncio.to_thread(index.upsert, vectors=upsert_data)

        return JSONResponse(
            status_code=200,
            content={"status": 200, "message": "Location renamed successfully."},
        )

    except Exception as e:
        raise e
