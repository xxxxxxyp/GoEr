from fastapi import APIRouter

from app.api.endpoints import auth, papers, subscriptions


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(subscriptions.router)
api_router.include_router(papers.router)
