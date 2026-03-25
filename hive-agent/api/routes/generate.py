"""Generate route handlers."""

from fastapi import APIRouter

router = APIRouter(prefix="/generate", tags=["generate"])
