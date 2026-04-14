from app.filter.base import BaseFilter, FilterResult
from app.filter.registry import registry
from app.models.topic import Topic


class SourceWeightFilter(BaseFilter):
    """来源权重过滤。按来源平台调整优先级分数，不 reject。"""

    name = "来源权重"
    filter_type = "source_weight"

    async def evaluate(self, topic: Topic, config: dict) -> FilterResult:
        weights = config.get("weights", {"weibo": 1.0, "baidu": 0.8, "zhihu": 1.2})
        weight = weights.get(topic.source, 1.0)

        return FilterResult(
            passed=True,
            priority_score=weight,
            reason=f"来源 {topic.source} 权重 {weight}",
        )


registry.register(SourceWeightFilter())
