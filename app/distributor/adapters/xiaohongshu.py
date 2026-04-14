"""小红书分发器（占位实现）。

小红书无官方发布 API，需通过 Playwright 自动化操作。
正式接入需：
1. 配置 Playwright + 小红书登录态
2. 自动化创建笔记流程
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class XiaohongshuDistributor(BaseDistributor):
    name = "小红书"
    platform = "xiaohongshu"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Xiaohongshu] Publishing: {content.title}")
        # TODO: 实现小红书发布逻辑（Playwright 自动化）
        return DistributeResult(
            platform=self.platform,
            success=False,
            error_message="小红书分发器需要 Playwright 自动化，尚未配置",
        )


registry.register(XiaohongshuDistributor())
