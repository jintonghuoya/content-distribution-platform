from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.distributor.registry import registry as distributor_registry
from app.models.distribution import DistributionRecord
from app.models.generated_content import GeneratedContent
from app.schemas.distributor import DistributionRecordResponse, DistributeTriggerResponse

router = APIRouter(prefix="/api/v1/distributors", tags=["distributors"])


@router.get("/")
async def list_distributors():
    """列出所有注册的分发器。"""
    return [
        {"name": dist.name, "platform": dist.platform}
        for dist in distributor_registry.get_all()
    ]


@router.post("/trigger", response_model=DistributeTriggerResponse)
async def trigger_distribute_all():
    """手动触发全量分发（所有 draft 内容）。"""
    from app.distributor.scheduler import distribute_published

    stats = await distribute_published()
    return DistributeTriggerResponse(**stats)


@router.post("/trigger/{content_id}", response_model=list[DistributionRecordResponse])
async def trigger_distribute_content(
    content_id: int,
    platform: str | None = Query(None, description="指定平台，如 wechat, toutiao"),
    db: AsyncSession = Depends(get_db),
):
    """为单条内容执行分发。"""
    content = await db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    from app.distributor.scheduler import distribute_single

    records = await distribute_single(content, platform)
    for record in records:
        db.add(record)
    await db.commit()
    for record in records:
        await db.refresh(record)

    return [DistributionRecordResponse.model_validate(r) for r in records]


@router.get("/records", response_model=list[DistributionRecordResponse])
async def list_distribution_records(
    content_id: int | None = Query(None),
    platform: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """分页查询分发记录。"""
    query = select(DistributionRecord)
    count_query = select(func.count(DistributionRecord.id))

    if content_id is not None:
        query = query.where(DistributionRecord.content_id == content_id)
        count_query = count_query.where(DistributionRecord.content_id == content_id)
    if platform:
        query = query.where(DistributionRecord.platform == platform)
        count_query = count_query.where(DistributionRecord.platform == platform)

    query = query.order_by(DistributionRecord.created_at.desc()).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()
    return [DistributionRecordResponse.model_validate(i) for i in items]
