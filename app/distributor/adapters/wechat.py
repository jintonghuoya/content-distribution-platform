"""微信公众号分发器（占位实现）。

正式接入需：
1. 在微信公众平台创建第三方平台应用，获取 app_id / app_secret
2. 通过 OAuth 获取 authorizer_access_token
3. 调用草稿箱 API 上传图文素材
4. 调用发布 API 发布到公众号
"""

from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent


class WeChatDistributor(BaseDistributor):
    name = "微信公众号"
    platform = "wechat"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[WeChat] Publishing: {content.title}")
        # TODO: 实现微信公众号发布逻辑
        return DistributeResult(
            platform=self.platform,
            success=False,
            error_message="微信公众号分发器尚未配置凭证，请在 .env 中设置 WECHAT_APP_ID 和 WECHAT_APP_SECRET",
        )


registry.register(WeChatDistributor())
