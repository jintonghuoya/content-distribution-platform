from abc import ABC, abstractmethod

from app.schemas.topic import TopicCreate


class BaseCollector(ABC):
    """采集器基类。所有平台采集器必须继承此类并实现 fetch()。"""

    name: str = ""
    source: str = ""

    @abstractmethod
    async def fetch(self, max_items: int = 50) -> list[TopicCreate]:
        """抓取热点话题列表，返回统一格式的 TopicCreate 列表。

        Args:
            max_items: 最大抓取条数。

        Returns:
            标准化的热点话题列表。
        """
        ...
