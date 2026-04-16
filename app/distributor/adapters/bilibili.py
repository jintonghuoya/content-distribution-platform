"""B站分发器（内容包模式）。

B站无公开的内容发布 API，采用内容包模式：
生成 B站专栏格式内容，用户复制后手动发布。
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class BilibiliDistributor(BaseDistributor):
    name = "B站"
    platform = "bilibili"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Bilibili] Packaging: {content.title}")

        body = content.body or ""

        return DistributeResult(
            platform=self.platform,
            success=True,
            mode="packaged",
            package_data={
                "title": content.title,
                "body": body,
                "char_count": len(body),
                "publish_url": "https://member.bilibili.com/article-text/home",
                "instructions": "打开 B站专栏投稿页，粘贴标题和正文",
            },
        )


registry.register(BilibiliDistributor())
