"""LangGraph API router."""

from fastapi import APIRouter
from app.api.v1.endpoints import upload, chat

api_router = APIRouter()
api_router.include_router(upload.router)
api_router.include_router(chat.router)