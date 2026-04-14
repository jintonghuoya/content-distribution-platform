"""B站分发器（占位实现）。

正式接入需：
1. 在 B站创作者中心获取 cookie 或 API 凭证
2. 调用 B站专栏发布 API
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class BilibiliDistributor(BaseDistributor):
    name = "B站"
    platform = "bilibili"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Bilibili] Publishing: {content.title}")
        # TODO: 实现 B站发布逻辑
        return DistributeResult(
            platform=self.platform,
            success=False,
            error_message="B站分发器尚未配置凭证",
        )


registry.register(BilibiliDistributor())
