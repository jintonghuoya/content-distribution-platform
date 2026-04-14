from loguru import logger

from app.revenue.base import BaseRevenueTracker


class RevenueTrackerRegistry:
    """收益追踪器注册中心。"""

    def __init__(self) -> None:
        self._trackers: dict[str, BaseRevenueTracker] = {}

    def register(self, tracker: BaseRevenueTracker) -> None:
        self._trackers[tracker.platform] = tracker
        logger.debug(f"Registered revenue tracker: {tracker.name} ({tracker.platform})")

    def get_all(self) -> list[BaseRevenueTracker]:
        return list(self._trackers.values())

    def get(self, platform: str) -> BaseRevenueTracker | None:
        return self._trackers.get(platform)


registry = RevenueTrackerRegistry()
