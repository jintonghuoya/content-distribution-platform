import hashlib
import re

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.collector.base import BaseCollector
from app.collector.registry import registry
from app.schemas.topic import TopicCreate


class BaiduCollector(BaseCollector):
    name = "百度热搜"
    source = "baidu"

    URL = "https://top.baidu.com/board?tab=realtime"

    async def fetch(self, max_items: int = 50) -> list[TopicCreate]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(self.URL, headers=headers)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        topics = []

        for i, item in enumerate(soup.select(".content_1YWBm")[:max_items]):
            title_el = item.select_one(".title_dIF3B")
            heat_el = item.select_one(".hot-index_1Bl1a")
            link_el = item.select_one("a")

            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            heat_text = heat_el.get_text(strip=True) if heat_el else "0"
            heat_value = int(re.sub(r"[^\d]", "", heat_text) or "0")
            url = link_el.get("href", "") if link_el else ""
            source_id = hashlib.md5(f"baidu:{title}".encode()).hexdigest()

            topics.append(
                TopicCreate(
                    title=title,
                    source=self.source,
                    source_id=source_id,
                    source_url=url,
                    rank=i + 1,
                    heat_value=heat_value,
                    raw_data={"title": title, "heat": heat_text, "url": url},
                )
            )
        logger.info(f"[Baidu] Fetched {len(topics)} topics")
        return topics


registry.register(BaiduCollector())
