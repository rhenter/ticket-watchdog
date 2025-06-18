import logging
import os
from threading import Lock
from typing import Dict, Any

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src import settings

logger = logging.getLogger(__name__)

# Global storage for SLA config
_sla_config: Dict[str, Any] = {}
_config_lock = Lock()


class SLAConfigHandler(FileSystemEventHandler):
    """
    Watchdog handler to reload SLA config when the YAML file changes.
    """

    def __init__(self, config_path: str):
        super().__init__()
        self._config_path = os.path.abspath(config_path)

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self._config_path:
            logger.info("Detected change in SLA config, reloading…")
            load_sla_config(self._config_path)


def load_sla_config(config_path: str = None) -> None:
    """
    Load SLA configuration from YAML into the global _sla_config dict.
    """
    path = config_path or os.getenv("SLA_CONFIG_PATH", "sla_config.yaml")
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        # Assuming top-level key "tiers"
        tiers = data.get("tiers", {})
        with _config_lock:
            _sla_config.clear()
            _sla_config.update(tiers)
        logger.info(f"SLA configuration loaded from {path}")
    except Exception as e:
        logger.error(f"Failed to load SLA config from {path}: {e}")


def get_sla_config() -> Dict[str, Any]:
    """
    Retrieve the current SLA configuration.
    """
    with _config_lock:
        return dict(_sla_config)


def start_config_watcher() -> None:
    """
    Starts a watchdog observer to reload SLA config on file changes.
    """
    path = settings.SLA_CONFIG_PATH
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handler = SLAConfigHandler(path)
    observer = Observer()
    observer.schedule(handler, directory, recursive=False)
    observer.daemon = True
    observer.start()
    logger.info(f"Started SLA config watcher on {path}")


# Initialize at import time
load_sla_config()
start_config_watcher()
