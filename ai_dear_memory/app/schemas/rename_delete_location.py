from typing import List
from pydantic import BaseModel


class RenameLocationRequest(BaseModel):
    user_id: int
    vector_ids: List[str]
    original_location: str
    modified_location: str


class DeleteLocationRequest(BaseModel):
    user_id: int
    vector_ids: List[str]
