from loguru import logger

from app.filter.base import BaseFilter


class FilterRegistry:
    """过滤规则注册中心：自动发现所有规则子类。"""

    def __init__(self) -> None:
        self._filters: dict[str, BaseFilter] = {}
        self._configs: dict[str, dict] = {}

    def register(self, f: BaseFilter) -> None:
        self._filters[f.filter_type] = f
        logger.debug(f"Registered filter: {f.name} ({f.filter_type})")

    def auto_discover(self) -> None:
        """导入 rules 包下的所有模块，触发子类注册。"""
        import importlib
        import pkgutil

        import app.filter.rules as rules_pkg

        for _, module_name, _ in pkgutil.iter_modules(rules_pkg.__path__):
            importlib.import_module(f"app.filter.rules.{module_name}")

    def get_all(self) -> list[BaseFilter]:
        return list(self._filters.values())

    def get_enabled(self) -> list[BaseFilter]:
        return [f for f in self._filters.values() if self._configs.get(f.filter_type, {}).get("enabled", True)]

    def set_config(self, filter_type: str, config: dict) -> None:
        self._configs[filter_type] = config

    def get_config(self, filter_type: str) -> dict:
        return self._configs.get(filter_type, {})


registry = FilterRegistry()
