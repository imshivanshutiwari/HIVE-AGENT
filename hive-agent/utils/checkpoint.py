"""Pipeline checkpoint manager for resumable runs."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CHECKPOINT_DIR = Path("assets/checkpoints")


class CheckpointManager:
    """Save and load pipeline checkpoints for resumable runs."""

    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else CHECKPOINT_DIR
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, name: str, state: Dict[str, Any]) -> str:
        """Save pipeline state checkpoint. Returns checkpoint path."""
        # Exclude non-serializable objects
        serializable = {}
        for key, value in state.items():
            if key in ("dependency_graph",):
                continue
            try:
                json.dumps(value)
                serializable[key] = value
            except (TypeError, ValueError):
                serializable[key] = str(value)

        checkpoint = {
            "name": name,
            "timestamp": time.time(),
            "state": serializable,
        }
        filepath = self.checkpoint_dir / f"{name}.json"
        with open(filepath, "w") as f:
            json.dump(checkpoint, f, indent=2, default=str)
        logger.info(f"Checkpoint saved: {filepath}")
        return str(filepath)

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint by name."""
        filepath = self.checkpoint_dir / f"{name}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r") as f:
            checkpoint = json.load(f)
        logger.info(f"Checkpoint loaded: {filepath}")
        return checkpoint.get("state", {})

    def exists(self, name: str) -> bool:
        return (self.checkpoint_dir / f"{name}.json").exists()

    def list_checkpoints(self) -> list:
        return [p.stem for p in self.checkpoint_dir.glob("*.json")]
