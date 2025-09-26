from typing import List
from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    user_id: int
    text: str


class EmbeddingResponse(BaseModel):
    vector_id: str
    location: str
    item: str


class SaveMemoryResponse(BaseModel):
    user_id: int
    success_message: str
    deleted_entries: List[str]
    items: List[EmbeddingResponse]
