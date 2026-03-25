"""Analyze route handlers."""
from fastapi import APIRouter
from api.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/analyze", tags=["analyze"])
