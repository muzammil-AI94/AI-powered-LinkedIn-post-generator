"""
Central API v1 router.

Why this module exists:
------------------------
Aggregates all v1 route modules into a single router.
main.py only needs to include this one router.

Benefits:
- easy to add new route modules
- clear versioning boundary
- cleaner main.py
"""

from fastapi import APIRouter

from app.api.v1.routes.post_routes import router as post_router
from app.api.v1.routes.posts_list_routes import router as posts_list_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(
    posts_list_router,
    tags=["Post History"],
)

v1_router.include_router(
    post_router,
    tags=["LinkedIn Posts"],
)
