from fastapi import APIRouter
from app.api.user_queries import user_queries_router

router = APIRouter()

# Include individual routers
router.include_router(
    user_queries_router, prefix="/user_queries", tags=["User Queries"]
)
