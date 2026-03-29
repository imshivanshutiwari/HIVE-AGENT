"""Pydantic models for API request/response schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="GitHub repo URL (owner/repo or full URL)")
    include_tests: bool = Field(True, description="Whether to generate tests")
    include_review: bool = Field(True, description="Whether to run code review")
    max_files: int = Field(100, description="Maximum files to process")


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str
    repo_url: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    stage: str
    message: str
    result: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    repo_url: str
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    doc_type: str = Field("function", description="function|class|module|readme")


class GenerateResponse(BaseModel):
    generated: str
    tokens_used: int
    model: str = "claude-sonnet-4-6"


class HealthResponse(BaseModel):
    status: str
    claude_connected: bool
    github_connected: bool
    codebert_loaded: bool
    langgraph_nodes: int
    version: str = "1.0.0"
