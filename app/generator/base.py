from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.models.topic import Topic


class GenerationResult(BaseModel):
    content_type: str
    title: str
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseGenerator(ABC):
    """内容生成器基类。所有生成器必须继承此类并实现 generate()。"""

    name: str = ""
    content_type: str = ""

    @abstractmethod
    async def generate(self, topic: Topic) -> GenerationResult:
        """基于 topic 生成内容。

        Args:
            topic: 已过滤的 Topic ORM 对象。

        Returns:
            GenerationResult，包含生成的标题、正文和元数据。
        """
        ...
