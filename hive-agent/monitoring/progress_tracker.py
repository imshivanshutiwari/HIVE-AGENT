"""Real-time analysis progress tracking."""
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressStage:
    name: str
    status: str  # "pending", "running", "complete", "error"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: float = 0.0
    message: str = ""

    @property
    def duration_seconds(self) -> float:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        if self.started_at:
            return time.time() - self.started_at
        return 0.0


class ProgressTracker:
    """Track and broadcast real-time analysis progress."""

    STAGES = ["Fetch", "Parse", "Analyze", "Similarity", "DocGen", "Review", "TestGen", "Evaluate"]

    def __init__(self):
        self.stages: Dict[str, ProgressStage] = {
            name: ProgressStage(name=name, status="pending") for name in self.STAGES
        }
        self.callbacks: List[Callable] = []
        self.log: List[str] = []

    def register_callback(self, callback: Callable) -> None:
        self.callbacks.append(callback)

    def start_stage(self, stage: str, message: str = "") -> None:
        if stage in self.stages:
            self.stages[stage].status = "running"
            self.stages[stage].started_at = time.time()
            self.stages[stage].message = message
            self._emit(f"[{stage}] Started: {message}")

    def complete_stage(self, stage: str, message: str = "") -> None:
        if stage in self.stages:
            self.stages[stage].status = "complete"
            self.stages[stage].completed_at = time.time()
            self.stages[stage].progress = 1.0
            self.stages[stage].message = message
            self._emit(f"[{stage}] Complete: {message}")

    def error_stage(self, stage: str, error: str) -> None:
        if stage in self.stages:
            self.stages[stage].status = "error"
            self.stages[stage].completed_at = time.time()
            self.stages[stage].message = error
            self._emit(f"[{stage}] Error: {error}")

    def update_progress(self, stage: str, progress: float) -> None:
        if stage in self.stages:
            self.stages[stage].progress = progress

    def _emit(self, message: str) -> None:
        entry = f"{time.strftime('%H:%M:%S')} {message}"
        self.log.append(entry)
        logger.info(message)
        for cb in self.callbacks:
            try:
                cb(entry)
            except Exception:
                pass

    def get_overall_progress(self) -> float:
        completed = sum(1 for s in self.stages.values() if s.status == "complete")
        return completed / len(self.stages)

    def get_status_dict(self) -> Dict:
        return {
            name: {
                "status": s.status,
                "progress": s.progress,
                "duration": s.duration_seconds,
                "message": s.message,
            }
            for name, s in self.stages.items()
        }
