from loguru import logger

from app.distributor.base import BaseDistributor


class DistributorRegistry:
    """分发器注册中心：自动发现所有分发器子类。"""

    def __init__(self) -> None:
        self._distributors: dict[str, BaseDistributor] = {}

    def register(self, dist: BaseDistributor) -> None:
        self._distributors[dist.platform] = dist
        logger.debug(f"Registered distributor: {dist.name} ({dist.platform})")

    def auto_discover(self) -> None:
        import importlib
        import pkgutil

        import app.distributor.adapters as adapters_pkg

        for _, module_name, _ in pkgutil.iter_modules(adapters_pkg.__path__):
            importlib.import_module(f"app.distributor.adapters.{module_name}")

    def get_all(self) -> list[BaseDistributor]:
        return list(self._distributors.values())

    def get(self, platform: str) -> BaseDistributor | None:
        return self._distributors.get(platform)


registry = DistributorRegistry()
