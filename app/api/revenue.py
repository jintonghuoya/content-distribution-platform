from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.revenue import RevenueRecord
from app.schemas.revenue import RevenueRecordResponse, RevenueSummary

router = APIRouter(prefix="/api/v1/revenue", tags=["revenue"])


@router.get("/records", response_model=list[RevenueRecordResponse])
async def list_revenue_records(
    platform: str | None = Query(None),
    content_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """分页查询收益记录。"""
    query = select(RevenueRecord)

    if platform:
        query = query.where(RevenueRecord.platform == platform)
    if content_id is not None:
        query = query.where(RevenueRecord.content_id == content_id)

    query = query.order_by(RevenueRecord.recorded_at.desc()).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()
    return [RevenueRecordResponse.model_validate(i) for i in items]


@router.get("/summary", response_model=RevenueSummary)
async def revenue_summary(
    platform: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
):
    """获取收益汇总数据。"""
    from app.revenue.scheduler import get_revenue_summary

    data = await get_revenue_summary(platform=platform, days=days)
    return RevenueSummary(**data)


@router.post("/collect")
async def trigger_revenue_collect():
    """手动触发收益数据采集。"""
    from app.revenue.scheduler import collect_revenue_all

    stats = await collect_revenue_all()
    return stats
