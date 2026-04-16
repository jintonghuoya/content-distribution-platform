"""今日头条分发器（内容包模式）。

头条号无公开的内容发布 API，采用内容包模式：
生成格式化内容，用户复制后手动发布。
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class ToutiaoDistributor(BaseDistributor):
    name = "今日头条"
    platform = "toutiao"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Toutiao] Packaging: {content.title}")

        body = content.body or ""
        # 头条正文上限约 20000 字，足够
        if len(body) > 20000:
            body = body[:19997] + "..."

        return DistributeResult(
            platform=self.platform,
            success=True,
            mode="packaged",
            package_data={
                "title": content.title,
                "body": body,
                "char_count": len(body),
                "publish_url": "https://mp.toutiao.com/profile_v4/graphic/publish",
                "instructions": "打开头条号创作平台，选择发表文章，粘贴标题和正文",
            },
        )


registry.register(ToutiaoDistributor())
