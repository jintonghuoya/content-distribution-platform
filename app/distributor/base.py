from abc import ABC, abstractmethod

from pydantic import BaseModel

from app.models.generated_content import GeneratedContent


class DistributeResult(BaseModel):
    platform: str
    success: bool
    platform_content_id: str = ""
    platform_url: str = ""
    error_message: str = ""


class BaseDistributor(ABC):
    """分发器基类。所有平台分发器必须继承此类并实现 publish()。"""

    name: str = ""
    platform: str = ""

    @abstractmethod
    async def publish(self, content: GeneratedContent) -> DistributeResult:
        """将生成内容发布到目标平台。

        Args:
            content: 待发布的 GeneratedContent ORM 对象。

        Returns:
            DistributeResult，包含是否成功、平台内容ID、URL 等。
        """
        ...

    async def check_status(self, platform_content_id: str) -> dict:
        """检查已发布内容的状态（阅读量等）。

        Args:
            platform_content_id: 平台侧内容 ID。

        Returns:
            平台返回的状态数据。
        """
        return {}
