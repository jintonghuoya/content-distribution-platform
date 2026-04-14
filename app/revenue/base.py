"""Revenue tracker 基类 — 从各平台采集收益/流量数据。"""

from abc import ABC, abstractmethod

from app.models.revenue import RevenueRecord


class BaseRevenueTracker(ABC):
    """收益追踪器基类。所有平台追踪器必须继承此类并实现 fetch_metrics()。"""

    name: str = ""
    platform: str = ""

    @abstractmethod
    async def fetch_metrics(self, platform_content_id: str) -> dict:
        """从平台获取内容的流量和收益数据。

        Args:
            platform_content_id: 平台侧内容 ID。

        Returns:
            dict，包含 views, likes, comments, shares, revenue_amount 等字段。
        """
        ...
