from fastapi import APIRouter
from app.api.v1.endpoints import auth, papers, chat, research, analysis

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
