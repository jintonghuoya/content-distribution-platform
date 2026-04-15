"""微博分发器。

通过 Cookie 模拟登录，调用微博移动端 API 发布微博。
用户需在平台配置中填入微博 Cookie。

Cookie 获取方式：
1. 手机浏览器登录 m.weibo.cn
2. 复制完整 Cookie（包含 SUB, _T_WM, MLOGIN, XSRF-TOKEN 等字段）
"""
import httpx
from loguru import logger

from app.distributor.base import BaseDistributor, DistributeResult
from app.distributor.registry import registry
from app.models.generated_content import GeneratedContent
from app.models.platform_config import PlatformConfig
from sqlalchemy import select

from app.database import async_session


async def _get_cookie() -> str:
    """从数据库获取微博 Cookie。"""
    async with async_session() as session:
        result = await session.execute(
            select(PlatformConfig).where(PlatformConfig.name == "weibo")
        )
        config = result.scalar_one_or_none()

    if not config or not config.cookie:
        raise ValueError("微博未配置 Cookie，请在平台配置中填写")

    return config.cookie


def _extract_xsrf_token(cookie: str) -> str:
    """从 Cookie 中提取 XSRF-TOKEN。"""
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("XSRF-TOKEN="):
            return part.split("=", 1)[1]
    return ""


async def _post_weibo(cookie: str, text: str) -> dict:
    """通过微博移动端 API 发布微博。"""
    url = "https://m.weibo.cn/api/statuses/update"

    xsrf_token = _extract_xsrf_token(cookie)
    logger.debug(f"[Weibo] Cookie length={len(cookie)}, XSRF-TOKEN={xsrf_token}")

    ua = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )

    headers = {
        "User-Agent": ua,
        "Referer": "https://m.weibo.cn/",
        "X-Requested-With": "XMLHttpRequest",
        "X-XSRF-TOKEN": xsrf_token,
        "Cookie": cookie,
        "Origin": "https://m.weibo.cn",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # 微博正文上限 2000 字
    if len(text) > 2000:
        text = text[:1997] + "..."

    data = {"content": text}

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        # 直接 POST，用用户原始 cookie 和 XSRF-TOKEN
        # 不做 warmup 请求，因为 warmup 会生成新的 session 和 XSRF-TOKEN，
        # 导致与用户原始登录 session 冲突
        resp = await client.post(url, headers=headers, data=data)

        logger.debug(f"[Weibo] Response status={resp.status_code}, body={resp.text[:500]}")

        try:
            result = resp.json()
        except Exception:
            logger.error(f"[Weibo] Response not JSON: {resp.text[:500]}")
            return {"ok": 0, "msg": f"非JSON响应: {resp.status_code}"}

    return result


class WeiboDistributor(BaseDistributor):
    name = "微博"
    platform = "weibo"

    async def publish(self, content: GeneratedContent) -> DistributeResult:
        logger.info(f"[Weibo] Publishing: {content.title}")

        try:
            cookie = await _get_cookie()

            # 组装正文：标题 + 内容
            body = content.body or ""
            text = f"{content.title}\n\n{body}" if content.title else body

            result = await _post_weibo(cookie, text)

            # 微博成功返回 {"ok": 1, "data": {"id": "..."}}
            if result.get("ok") == 1:
                weibo_id = str(result.get("data", {}).get("id", ""))
                weibo_url = f"https://m.weibo.cn/detail/{weibo_id}" if weibo_id else ""
                logger.info(f"[Weibo] Published: {weibo_url}")
                return DistributeResult(
                    platform=self.platform,
                    success=True,
                    platform_content_id=weibo_id,
                    platform_url=weibo_url,
                )
            else:
                error_msg = result.get("msg", result.get("errmsg", str(result)))
                logger.error(f"[Weibo] Publish failed: {error_msg}")
                return DistributeResult(
                    platform=self.platform,
                    success=False,
                    error_message=f"微博发布失败: {error_msg}",
                )

        except ValueError as e:
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"[Weibo] Unexpected error: {e}")
            return DistributeResult(
                platform=self.platform,
                success=False,
                error_message=f"微博发布异常: {e}",
            )


registry.register(WeiboDistributor())
