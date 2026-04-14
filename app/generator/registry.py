from loguru import logger

from app.generator.base import BaseGenerator


class GeneratorRegistry:
    """生成器注册中心：自动发现所有生成器子类。"""

    def __init__(self) -> None:
        self._generators: dict[str, BaseGenerator] = {}

    def register(self, gen: BaseGenerator) -> None:
        self._generators[gen.content_type] = gen
        logger.debug(f"Registered generator: {gen.name} ({gen.content_type})")

    def auto_discover(self) -> None:
        """导入 prompts 包下的所有模块，触发子类注册。"""
        import importlib
        import pkgutil

        import app.generator.prompts as prompts_pkg

        for _, module_name, _ in pkgutil.iter_modules(prompts_pkg.__path__):
            importlib.import_module(f"app.generator.prompts.{module_name}")

    def get_all(self) -> list[BaseGenerator]:
        return list(self._generators.values())

    def get(self, content_type: str) -> BaseGenerator | None:
        return self._generators.get(content_type)


registry = GeneratorRegistry()
