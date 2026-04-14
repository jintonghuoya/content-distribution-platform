from app.filter.base import BaseFilter, FilterResult
from app.filter.registry import registry
from app.models.topic import Topic


class HeatThresholdFilter(BaseFilter):
    """热度阈值过滤。热度值低于阈值则 reject，高于阈值按比例计算优先级。"""

    name = "热度阈值"
    filter_type = "heat_threshold"

    async def evaluate(self, topic: Topic, config: dict) -> FilterResult:
        min_heat = config.get("min_heat", 0)
        max_heat = config.get("max_heat", 100000)
        heat = topic.heat_value or 0

        if heat < min_heat:
            return FilterResult(
                passed=False,
                reason=f"热度值 {heat} 低于阈值 {min_heat}",
            )

        # 按热度比例算分：0.5 ~ 5.0
        ratio = min(heat / max(max_heat, 1), 1.0)
        score = 0.5 + ratio * 4.5

        return FilterResult(passed=True, priority_score=score)


registry.register(HeatThresholdFilter())
