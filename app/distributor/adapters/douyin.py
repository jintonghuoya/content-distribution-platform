"""抖音分发器（内容包模式）。

抖音开放平台有视频发布 API，但需要应用审核和资质。
当前采用内容包模式，未来可升级为自动发布。
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class DouyinDistributor(BaseDistributor):
    name = "抖音"
    platform = "douyin"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Douyin] Packaging: {content.title}")

        body = content.body or ""
        # 抖音图文限 1000 字
        if len(body) > 1000:
            body = body[:997] + "..."

        return DistributeResult(
            platform=self.platform,
            success=True,
            mode="packaged",
            package_data={
                "title": content.title,
                "body": body,
                "char_count": len(body),
                "publish_url": "https://creator.douyin.com/creator-micro/content/upload",
                "instructions": "打开抖音创作者中心，选择发布图文，粘贴标题和正文（需手动添加图片）",
            },
        )


registry.register(DouyinDistributor())
