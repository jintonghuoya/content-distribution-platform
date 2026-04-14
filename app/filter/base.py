from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.models.topic import Topic


class FilterResult(BaseModel):
    passed: bool
    category: str | None = None
    priority_score: float = 0.0
    reason: str = ""


class BaseFilter(ABC):
    """过滤规则基类。所有规则必须继承此类并实现 evaluate()。"""

    name: str = ""
    filter_type: str = ""

    @abstractmethod
    async def evaluate(self, topic: Topic, config: dict) -> FilterResult:
        """评估一条 topic，返回过滤结果。

        Args:
            topic: 待评估的 Topic ORM 对象。
            config: 该规则的运行时配置（从 filter_rules 表或 YAML 加载）。

        Returns:
            FilterResult，包含是否通过、分类、优先级分数和原因。
        """
        ...
