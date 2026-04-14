"""今日头条分发器（占位实现）。

正式接入需：
1. 在头条号开放平台创建应用
2. 获取 access_token
3. 调用内容发布 API
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class ToutiaoDistributor(BaseDistributor):
    name = "今日头条"
    platform = "toutiao"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Toutiao] Publishing: {content.title}")
        # TODO: 实现头条发布逻辑
        return DistributeResult(
            platform=self.platform,
            success=False,
            error_message="今日头条分发器尚未配置凭证",
        )


registry.register(ToutiaoDistributor())
