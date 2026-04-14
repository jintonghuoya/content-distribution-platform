import hashlib

import httpx
from loguru import logger

from app.collector.base import BaseCollector
from app.collector.registry import registry
from app.schemas.topic import TopicCreate


class WeiboCollector(BaseCollector):
    name = "微博热搜"
    source = "weibo"

    API_URL = "https://weibo.com/ajax/side/hotSearch"

    async def fetch(self, max_items: int = 50) -> list[TopicCreate]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://weibo.com/",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(self.API_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", {}).get("realtime", [])
        topics = []
        for i, item in enumerate(items[:max_items]):
            title = item.get("word", "")
            if not title:
                continue
            source_id = hashlib.md5(f"weibo:{title}".encode()).hexdigest()
            topics.append(
                TopicCreate(
                    title=title,
                    source=self.source,
                    source_id=source_id,
                    source_url=f"https://s.weibo.com/weibo?q=%23{title}%23",
                    rank=i + 1,
                    heat_value=item.get("num", 0),
                    raw_data=item,
                )
            )
        logger.info(f"[Weibo] Fetched {len(topics)} topics")
        return topics


registry.register(WeiboCollector())
