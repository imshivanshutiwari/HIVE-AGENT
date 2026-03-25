"""Status route handlers."""
from fastapi import APIRouter
from api.schemas import JobStatusResponse

router = APIRouter(prefix="/status", tags=["status"])
