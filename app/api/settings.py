from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.platform_config import PlatformConfig
from app.schemas.platform_config import PlatformConfigCreate, PlatformConfigResponse

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

# Default platforms to seed on first access
DEFAULT_PLATFORMS = [
    {"name": "weibo", "display_name": "微博"},
    {"name": "wechat", "display_name": "微信公众号"},
    {"name": "toutiao", "display_name": "今日头条"},
    {"name": "xiaohongshu", "display_name": "小红书"},
    {"name": "bilibili", "display_name": "B站"},
    {"name": "douyin", "display_name": "抖音"},
]


@router.get("/platforms", response_model=list[PlatformConfigResponse])
async def list_platforms(db: AsyncSession = Depends(get_db)):
    """获取所有平台配置。"""
    result = await db.execute(select(PlatformConfig).order_by(PlatformConfig.id))
    platforms = result.scalars().all()

    if not platforms:
        # Seed default platforms on first access
        for p in DEFAULT_PLATFORMS:
            db.add(PlatformConfig(name=p["name"], display_name=p["display_name"]))
        await db.commit()
        result = await db.execute(select(PlatformConfig).order_by(PlatformConfig.id))
        platforms = result.scalars().all()

    return platforms


@router.put("/platforms/{name}", response_model=PlatformConfigResponse)
async def upsert_platform(
    name: str,
    body: PlatformConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建或更新平台配置。"""
    result = await db.execute(select(PlatformConfig).where(PlatformConfig.name == name))
    platform = result.scalar_one_or_none()

    if platform:
        platform.display_name = body.display_name or platform.display_name
        platform.api_key = body.api_key
        platform.cookie = body.cookie
        platform.app_secret = body.app_secret
        platform.app_id = body.app_id
        if body.extra is not None:
            platform.extra = body.extra
    else:
        platform = PlatformConfig(
            name=name,
            display_name=body.display_name or name,
            api_key=body.api_key,
            cookie=body.cookie,
            app_secret=body.app_secret,
            app_id=body.app_id,
            extra=body.extra,
        )
        db.add(platform)

    await db.commit()
    await db.refresh(platform)
    return platform
