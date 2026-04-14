"""抖音分发器（占位实现）。

正式接入需：
1. 在抖音开放平台创建应用
2. 获取 access_token
3. 调用视频/图文发布 API
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class DouyinDistributor(BaseDistributor):
    name = "抖音"
    platform = "douyin"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Douyin] Publishing: {content.title}")
        # TODO: 实现抖音发布逻辑
        return DistributeResult(
            platform=self.platform,
            success=False,
            error_message="抖音分发器尚未配置凭证",
        )


registry.register(DouyinDistributor())
