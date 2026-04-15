"""微信公众号分发器。

流程：
1. 用 app_id + app_secret 获取 access_token
2. 调用 /cgi-bin/draft/add 上传图文到草稿箱
3. 调用 /cgi-bin/freepublish/submit 发布
4. 调用 /cgi-bin/freepublish/get 轮询发布状态
"""

import httpx
from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent
from app.models.platform_config import PlatformConfig
from sqlalchemy import select

from app.database import async_session

BASE_URL = "https://api.weixin.qq.com"


async def _get_access_token() -> str:
    """从数据库获取微信配置，换取 access_token。"""
    async with async_session() as session:
        result = await session.execute(
            select(PlatformConfig).where(PlatformConfig.name == "wechat")
        )
        config = result.scalar_one_or_none()

    if not config or not config.app_id or not config.app_secret:
        raise ValueError("微信公众号未配置 app_id / app_secret，请在平台配置中填写")

    url = f"{BASE_URL}/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": config.app_id,
        "secret": config.app_secret,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    if "access_token" not in data:
        raise ValueError(f"获取 access_token 失败: {data.get('errmsg', data)}")

    return data["access_token"]


async def _add_draft(access_token: str, title: str, body: str) -> str:
    """上传图文到草稿箱，返回 media_id。"""
    url = f"{BASE_URL}/cgi-bin/draft/add?access_token={access_token}"

    # 微信公众号图文格式
    article = {
        "articles": [
            {
                "title": title,
                "author": "",
                "digest": body[:120].replace("\n", " ") if body else "",
                "content": body or "",
                "content_source_url": "",
                "need_open_comment": 0,
                "only_fans_can_comment": 0,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=article)
        data = resp.json()

    if "media_id" not in data:
        raise ValueError(f"添加草稿失败: {data.get('errmsg', data)}")

    return data["media_id"]


async def _publish(access_token: str, media_id: str) -> str:
    """发布草稿，返回 publish_id。"""
    url = f"{BASE_URL}/cgi-bin/freepublish/submit?access_token={access_token}"
    payload = {"media_id": media_id}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    if "publish_id" not in data:
        raise ValueError(f"发布失败: {data.get('errmsg', data)}")

    return str(data["publish_id"])


async def _check_publish_status(access_token: str, publish_id: str) -> dict:
    """查询发布状态。"""
    url = f"{BASE_URL}/cgi-bin/freepublish/get?access_token={access_token}"
    payload = {"publish_id": publish_id}

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, json=payload)
        data = resp.json()

    return data


class WeChatDistributor(BaseDistributor):
    name = "微信公众号"
    platform = "wechat"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[WeChat] Publishing: {content.title}")

        try:
            # 1. 获取 access_token
            access_token = await _get_access_token()

            # 2. 上传到草稿箱
            body = content.body or ""
            media_id = await _add_draft(access_token, content.title, body)
            logger.info(f"[WeChat] Draft created: {media_id}")

            # 3. 发布
            publish_id = await _publish(access_token, media_id)
            logger.info(f"[WeChat] Published, publish_id: {publish_id}")

            return DistributeResult(
                platform=self.platform,
                success=True,
                platform_content_id=publish_id,
                platform_url="",
                error_message="",
            )

        except ValueError as e:
            logger.error(f"[WeChat] {e}")
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"[WeChat] Unexpected error: {e}")
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=f"微信发布异常: {e}",
            )


registry.register(WeChatDistributor())
