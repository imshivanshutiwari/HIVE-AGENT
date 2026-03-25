"""FastAPI server for HIVE-AGENT."""
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    AnalyzeRequest, AnalyzeResponse,
    GenerateRequest, GenerateResponse,
    HealthResponse, JobStatusResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="HIVE-AGENT API",
    description="Autonomous Codebase Analyst and Documentation Generator",
    version="1.0.0",
)

_cors_origins_env = os.environ.get("CORS_ALLOWED_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store
_jobs: Dict[str, Dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=4)


def _run_pipeline_job(job_id: str, repo_url: str) -> None:
    """Run pipeline in background thread."""
    from pipeline.main import run_pipeline
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["progress"] = 0.1
    try:
        result = run_pipeline(repo_url)
        _jobs[job_id]["status"] = "complete"
        _jobs[job_id]["progress"] = 1.0
        _jobs[job_id]["result"] = {
            "docs_generated": len(result.get("generated_docs", {})),
            "tests_generated": len(result.get("generated_tests", {})),
            "tokens_used": result.get("claude_tokens_used", 0),
            "security_issues": len(result.get("security_issues", [])),
            "pipeline_trace": result.get("pipeline_trace", []),
            "doc_quality_scores": result.get("doc_quality_scores", {}),
        }
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["message"] = str(e)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health."""
    claude_ok = bool(os.environ.get("ANTHROPIC_API_KEY"))
    github_ok = bool(os.environ.get("GITHUB_TOKEN"))
    return HealthResponse(
        status="healthy",
        claude_connected=claude_ok,
        github_connected=github_ok,
        codebert_loaded=False,  # lazy loaded
        langgraph_nodes=8,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repo(request: AnalyzeRequest):
    """Start async repository analysis job."""
    repo_url = request.repo_url
    if not repo_url.startswith("https://"):
        repo_url = f"https://github.com/{repo_url}"

    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "stage": "Queued",
        "message": f"Analysis queued for {repo_url}",
        "result": None,
        "repo_url": repo_url,
    }
    _executor.submit(_run_pipeline_job, job_id, repo_url)
    return AnalyzeResponse(
        job_id=job_id,
        status="queued",
        repo_url=repo_url,
        message=f"Analysis started with job_id={job_id}",
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    """Get status of an analysis job."""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job = _jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0.0),
        stage=job.get("stage", ""),
        message=job.get("message", ""),
        result=job.get("result"),
    )


@app.post("/generate", response_model=GenerateResponse)
async def generate_doc(request: GenerateRequest):
    """Generate documentation for a specific function/class/module."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    from generation.claude_client import ClaudeClient
    claude = ClaudeClient()
    prompt = (
        f"Generate {request.doc_type} documentation for {request.function_name or 'the module'} "
        f"in {request.repo_url}."
    )
    text, tokens = claude.generate(prompt)
    return GenerateResponse(generated=text, tokens_used=tokens)


if __name__ == "__main__":
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)
