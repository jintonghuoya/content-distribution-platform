"""微博分发器。

通过 HTTP 调用宿主机上的 Playwright Browser Service 发布微博。
宿主机服务地址通过环境变量 BROWSER_SERVICE_URL 配置，默认 http://host.docker.internal:8001。

首次使用需在宿主机上运行登录脚本保存登录态（见 browser-service/ 目录）。
"""

import httpx
from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent

BROWSER_SERVICE_URL = "http://host.docker.internal:8001"


def _format_text(content: GeneratedContent) -> str:
    """组装微博正文，2000 字截断。"""
    body = content.body or ""
    if len(body) > 2000:
        body = body[:1997] + "..."
    return body


class WeiboDistributor(BaseDistributor):
    name = "微博"
    platform = "weibo"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Weibo] Publishing via browser service: {content.title}")

        body = _format_text(content)

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{BROWSER_SERVICE_URL}/publish/weibo",
                    json={"title": "", "body": body},
                )
                data = resp.json()
        except httpx.ConnectError:
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message="无法连接 Playwright Browser Service，请确认宿主机服务已启动 (port 8001)",
            )
        except Exception as e:
            logger.error(f"[Weibo] Request error: {e}")
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=f"微博发布请求异常: {e}",
            )

        if data.get("success"):
            return DistributeResult(
                platform=self.platform,
                success=True,
                platform_url=data.get("platform_url", ""),
            )
        else:
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=data.get("error_message", "未知错误"),
            )


registry.register(WeiboDistributor())
