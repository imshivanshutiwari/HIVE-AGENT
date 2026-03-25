"""Generate route handlers."""
from fastapi import APIRouter
from api.schemas import GenerateRequest, GenerateResponse

router = APIRouter(prefix="/generate", tags=["generate"])
