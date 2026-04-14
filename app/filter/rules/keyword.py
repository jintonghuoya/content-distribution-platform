from app.filter.base import BaseFilter, FilterResult
from app.filter.registry import registry
from app.models.topic import Topic


class KeywordBlacklistFilter(BaseFilter):
    """关键词黑名单过滤。标题命中任何黑名单关键词则 reject。"""

    name = "关键词黑名单"
    filter_type = "keyword_blacklist"

    async def evaluate(self, topic: Topic, config: dict) -> FilterResult:
        blacklist = config.get("keywords", [])
        title = topic.title or ""

        for keyword in blacklist:
            if keyword.lower() in title.lower():
                return FilterResult(
                    passed=False,
                    reason=f"标题命中黑名单关键词: {keyword}",
                )

        return FilterResult(passed=True, priority_score=1.0)


registry.register(KeywordBlacklistFilter())
