"""YAML configuration loader."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "configs"


class ConfigLoader:
    """Load and cache YAML configuration files."""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load(self, name: str) -> Dict[str, Any]:
        """Load a config file by name (without .yaml extension)."""
        if name in self._cache:
            return self._cache[name]

        filepath = self.config_dir / f"{name}.yaml"
        if not filepath.exists():
            logger.warning(f"Config file not found: {filepath}")
            return {}

        with open(filepath, "r") as f:
            config = yaml.safe_load(f) or {}
        self._cache[name] = config
        return config

    def get(self, config_name: str, key: str, default: Any = None) -> Any:
        config = self.load(config_name)
        return config.get(key, default)

    @property
    def agent_config(self) -> Dict[str, Any]:
        return self.load("agent_config")

    @property
    def analysis_config(self) -> Dict[str, Any]:
        return self.load("analysis_config")

    @property
    def github_config(self) -> Dict[str, Any]:
        return self.load("github_config")

    @property
    def generation_config(self) -> Dict[str, Any]:
        return self.load("generation_config")

    @property
    def evaluation_config(self) -> Dict[str, Any]:
        return self.load("evaluation_config")
