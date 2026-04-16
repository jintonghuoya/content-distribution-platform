"""小红书分发器。

通过 HTTP 调用宿主机上的 Playwright Browser Service 发布小红书笔记。
宿主机服务地址通过环境变量 BROWSER_SERVICE_URL 配置，默认 http://host.docker.internal:8001。

首次使用需在宿主机上运行登录脚本保存登录态（见 browser-service/ 目录）。
"""

import httpx
from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent

BROWSER_SERVICE_URL = "http://host.docker.internal:8001"


class XiaohongshuDistributor(BaseDistributor):
    name = "小红书"
    platform = "xiaohongshu"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[XHS] Publishing via browser service: {content.title}")

        title = (content.title or "")[:20]
        body = (content.body or "")[:1000]

        # 提取标签
        metadata = content.metadata_ or {}
        tags = metadata.get("tags", [])[:5]
        if tags:
            tag_str = " ".join(f"#{t}#" for t in tags)
            body = f"{body}\n\n{tag_str}"

        url = f"{BROWSER_SERVICE_URL}/publish/xiaohongshu"
        payload = {"title": title, "body": body}
        logger.info(f"[XHS] POST {url} title={title!r} body_len={len(body)}")

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload)
                logger.info(f"[XHS] Response status={resp.status_code} body={resp.text[:200]}")
                data = resp.json()
        except httpx.ConnectError:
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message="无法连接 Playwright Browser Service，请确认宿主机服务已启动 (port 8001)",
            )
        except Exception as e:
            logger.error(f"[XHS] Request error: {e}")
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=f"小红书发布请求异常: {e}",
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


# registry.register(XiaohongshuDistributor())  # 暂时禁用，Browser Service 小红书发布未稳定
