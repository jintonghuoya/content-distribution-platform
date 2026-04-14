from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.topic import Topic, TopicStatus
from app.schemas.topic import CollectResponse, TopicListResponse, TopicResponse

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
async def list_topics(
    source: str | None = Query(None, description="按来源平台过滤"),
    status: TopicStatus | None = Query(None, description="按状态过滤"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取热点话题列表，支持按来源和状态过滤。"""
    query = select(Topic)
    count_query = select(func.count(Topic.id))

    if source:
        query = query.where(Topic.source == source)
        count_query = count_query.where(Topic.source == source)
    if status:
        query = query.where(Topic.status == status)
        count_query = count_query.where(Topic.status == status)

    query = query.order_by(Topic.collected_at.desc()).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    topics = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return TopicListResponse(
        total=total,
        items=[TopicResponse.model_validate(t) for t in topics],
    )


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个热点话题详情。"""
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicResponse.model_validate(topic)


@router.post("/collect", response_model=CollectResponse)
async def trigger_collect(db: AsyncSession = Depends(get_db)):
    """手动触发一次全量采集。"""
    from app.collector.registry import registry
    from app.collector.scheduler import collect_all

    # 确保采集器已注册
    if not registry._collectors:
        registry.load_config()
        registry.auto_discover()

    results = await collect_all()
    return CollectResponse(results=results, message=f"Collected from {len(results)} sources")
