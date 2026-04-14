import hashlib

import httpx
from loguru import logger

from app.collector.base import BaseCollector
from app.collector.registry import registry
from app.schemas.topic import TopicCreate


class ZhihuCollector(BaseCollector):
    name = "知乎热榜"
    source = "zhihu"

    API_URL = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"

    async def fetch(self, max_items: int = 50) -> list[TopicCreate]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.zhihu.com/hot",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(self.API_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", [])
        topics = []
        for i, item in enumerate(items[:max_items]):
            target = item.get("target", {})
            title = target.get("title", "")
            if not title:
                continue

            heat = item.get("detail_text", "")
            heat_value = 0
            if "万" in heat:
                try:
                    heat_value = int(float(heat.replace("万热度", "").strip()) * 10000)
                except ValueError:
                    pass

            url = target.get("url", "").replace("api.", "www.").replace("/questions/", "/question/")
            source_id = hashlib.md5(f"zhihu:{title}".encode()).hexdigest()

            topics.append(
                TopicCreate(
                    title=title,
                    source=self.source,
                    source_id=source_id,
                    source_url=url,
                    rank=i + 1,
                    heat_value=heat_value,
                    raw_data=item,
                )
            )
        logger.info(f"[Zhihu] Fetched {len(topics)} topics")
        return topics


registry.register(ZhihuCollector())
