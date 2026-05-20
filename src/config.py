# config.py
# Configuration management for the Compiler Analysis System
#
# Loads config.json at startup and provides safe access to all thresholds,
# weights, and normalization parameters.
#
# Design:
#   - Load once at module import time
#   - Provide typed accessor functions
#   - Fall back to reasonable defaults if config is missing
#   - Log load status for debugging

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


# Default configuration (used if config.json is missing)
DEFAULT_CONFIG = {
    "thresholds": {
        "token_high": 30,
        "rule_high": 50,
        "depth_high": 10,
        "node_high": 60,
        "cost_high": 100,
        "print_heavy": 3,
        "assign_heavy": 5,
        "memory_high_kb": 512,
        "time_high_ms": 50,
    },
    "weights": {
        "token": 0.20,
        "depth": 0.30,
        "rules": 0.25,
        "time": 0.15,
        "memory": 0.10,
    },
    "normalization": {
        "token_max": 200,
        "depth_max": 20,
        "rules_max": 150,
        "time_max_ms": 100,
        "memory_max_kb": 2048,
    },
}


class ConfigManager:
    """
    Centralized configuration manager for the compiler analysis system.
    
    Loads config.json once at initialization and provides safe,
    typed access to all configuration values with sensible defaults.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to config.json. If None, looks for:
                1. COMPILER_CONFIG environment variable
                2. backend/config.json relative to this file
                3. Falls back to DEFAULT_CONFIG
        """
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._loaded_from: str = "defaults"

        if config_path is None:
            # Try environment variable
            env_path = os.getenv("COMPILER_CONFIG")
            if env_path:
                config_path = Path(env_path)
            else:
                # Look for config.json in backend/ directory
                # This file is in src/, so go up one level and into backend/
                this_file = Path(__file__)
                backend_config = this_file.parent.parent / "backend" / "config.json"
                if backend_config.exists():
                    config_path = backend_config

        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded = json.load(f)
                    # Deep merge: overlay loaded config over defaults
                    self._merge_config(self._config, loaded)
                    self._loaded_from = str(config_path)
            except Exception as e:
                print(f"[CONFIG] Warning: Failed to load {config_path}: {e}")
                print(f"[CONFIG] Using default configuration.")

    def _merge_config(self, base: Dict, overlay: Dict) -> None:
        """Recursively merge overlay config into base config."""
        for key, value in overlay.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get_threshold(self, name: str) -> float:
        """Get a threshold value by name."""
        return self._config["thresholds"].get(name, DEFAULT_CONFIG["thresholds"].get(name, 0))

    def get_weight(self, name: str) -> float:
        """Get a cost weight by name."""
        return self._config["weights"].get(name, DEFAULT_CONFIG["weights"].get(name, 0))

    def get_normalization(self, name: str) -> float:
        """Get a normalization max value by name."""
        return self._config["normalization"].get(name, DEFAULT_CONFIG["normalization"].get(name, 1))

    def get_full_config(self) -> Dict[str, Any]:
        """Return the full merged configuration dict."""
        return self._config.copy()

    def get_loaded_from(self) -> str:
        """Return the source of the loaded configuration."""
        return self._loaded_from


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get or initialize the global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        print(f"[CONFIG] Loaded from: {_config_manager.get_loaded_from()}")
    return _config_manager


# Convenience functions for backward compatibility
def get_threshold(name: str) -> float:
    """Get a threshold value by name."""
    return get_config().get_threshold(name)


def get_weight(name: str) -> float:
    """Get a cost weight by name."""
    return get_config().get_weight(name)


def get_normalization(name: str) -> float:
    """Get a normalization max value by name."""
    return get_config().get_normalization(name)
