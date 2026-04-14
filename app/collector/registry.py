from pathlib import Path

import yaml
from loguru import logger

from app.collector.base import BaseCollector


class CollectorRegistry:
    """采集器注册中心：自动发现所有采集器子类，并按 sources.yaml 控制启用/禁用。"""

    def __init__(self) -> None:
        self._collectors: dict[str, BaseCollector] = {}
        self._config: dict = {}

    def load_config(self, config_path: Path | None = None) -> None:
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "sources.yaml"
        with open(config_path) as f:
            self._config = yaml.safe_load(f) or {}

    def register(self, collector: BaseCollector) -> None:
        self._collectors[collector.source] = collector
        logger.debug(f"Registered collector: {collector.name} ({collector.source})")

    def auto_discover(self) -> None:
        """导入 sources 包下的所有模块，触发子类注册。"""
        import importlib
        import pkgutil

        import app.collector.sources as sources_pkg

        for _, module_name, _ in pkgutil.iter_modules(sources_pkg.__path__):
            importlib.import_module(f"app.collector.sources.{module_name}")

    def get_enabled(self) -> list[BaseCollector]:
        sources_cfg = self._config.get("sources", {})
        enabled = []
        for source, collector in self._collectors.items():
            cfg = sources_cfg.get(source, {})
            if cfg.get("enabled", False):
                enabled.append(collector)
        return enabled

    def get_config(self, source: str) -> dict:
        return self._config.get("sources", {}).get(source, {})


registry = CollectorRegistry()
