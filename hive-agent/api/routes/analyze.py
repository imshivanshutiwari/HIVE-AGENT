"""Analyze route handlers."""

from fastapi import APIRouter

router = APIRouter(prefix="/analyze", tags=["analyze"])
