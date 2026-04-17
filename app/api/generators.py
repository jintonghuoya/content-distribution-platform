from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.generator.registry import registry as generator_registry
from app.models.distribution import DistributionRecord
from app.models.generated_content import GeneratedContent
from app.models.topic import Topic
from app.schemas.generator import (
    GeneratedContentListResponse,
    GeneratedContentResponse,
    GenerateTriggerResponse,
)

router = APIRouter(prefix="/api/v1/generators", tags=["generators"])


@router.get("/")
async def list_generators():
    """列出所有注册的生成器。"""
    return [
        {"name": gen.name, "content_type": gen.content_type}
        for gen in generator_registry.get_all()
    ]


@router.post("/trigger", response_model=GenerateTriggerResponse)
async def trigger_generate_all():
    """异步触发全量生成（所有 filtered topics），通过 Celery 后台执行。"""
    from app.workers.generator_worker import generate_filtered_task

    generate_filtered_task.delay()
    return GenerateTriggerResponse(total=0, generated=0, message="生成任务已提交，后台执行中")


@router.post("/trigger/{topic_id}")
async def trigger_generate_topic(
    topic_id: int,
    generator: str | None = Query(None, description="指定生成器类型，如 article, social_post"),
    db: AsyncSession = Depends(get_db),
):
    """异步为单条 topic 生成内容，通过 Celery 后台执行。"""
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    from app.workers.generator_worker import generate_topic_task

    generate_topic_task.delay(topic_id, generator)
    return {"topic_id": topic_id, "message": "生成任务已提交，后台执行中"}


@router.get("/content", response_model=GeneratedContentListResponse)
async def list_generated_content(
    topic_id: int | None = Query(None, description="按 topic ID 过滤"),
    content_type: str | None = Query(None, description="按内容类型过滤"),
    status: str | None = Query(None, description="按状态过滤"),
    exclude_published: bool = Query(False, description="排除所有平台已分发完的内容"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """分页查询已生成的内容。"""
    query = select(GeneratedContent)
    count_query = select(func.count(GeneratedContent.id))

    if topic_id is not None:
        query = query.where(GeneratedContent.topic_id == topic_id)
        count_query = count_query.where(GeneratedContent.topic_id == topic_id)
    if content_type:
        query = query.where(GeneratedContent.content_type == content_type)
        count_query = count_query.where(GeneratedContent.content_type == content_type)
    if status:
        query = query.where(GeneratedContent.status == status)
        count_query = count_query.where(GeneratedContent.status == status)

    if exclude_published:
        # 排除所有注册平台都已成功分发的内容
        from app.distributor.registry import registry as dist_registry
        platforms = [d.platform for d in dist_registry.get_all()]
        if platforms:
            for platform in platforms:
                subq = (
                    select(DistributionRecord.id)
                    .where(
                        DistributionRecord.content_id == GeneratedContent.id,
                        DistributionRecord.platform == platform,
                        DistributionRecord.success.is_(True),
                    )
                    .correlate(GeneratedContent)
                    .exists()
                )
                query = query.where(not_(subq))
                count_query = count_query.where(not_(subq))

    query = query.order_by(GeneratedContent.created_at.desc()).offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    items = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return GeneratedContentListResponse(
        total=total,
        items=[GeneratedContentResponse.model_validate(i) for i in items],
    )


@router.get("/content/{content_id}", response_model=GeneratedContentResponse)
async def get_generated_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """获取单条生成内容。"""
    content = await db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return GeneratedContentResponse.model_validate(content)


@router.put("/content/{content_id}/publish", response_model=GeneratedContentResponse)
async def publish_generated_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """将生成内容状态改为 published。"""
    content = await db.get(GeneratedContent, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    content.status = "published"
    await db.commit()
    await db.refresh(content)
    return GeneratedContentResponse.model_validate(content)
