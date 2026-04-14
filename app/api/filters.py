from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.filter.registry import registry as filter_registry
from app.models.filter_rule import FilterRule
from app.models.topic import Topic, TopicStatus
from app.schemas.filter import (
    FilterRuleCreate,
    FilterRuleResponse,
    FilterTriggerResponse,
)

router = APIRouter(prefix="/api/v1/filters", tags=["filters"])


@router.get("/rules", response_model=list[FilterRuleResponse])
async def list_filter_rules(db: AsyncSession = Depends(get_db)):
    """列出所有过滤规则（注册的 + 数据库中的）。"""
    result = await db.execute(select(FilterRule).order_by(FilterRule.run_order))
    return result.scalars().all()


@router.post("/rules", response_model=FilterRuleResponse)
async def create_filter_rule(body: FilterRuleCreate, db: AsyncSession = Depends(get_db)):
    """创建一条过滤规则。"""
    rule = FilterRule(
        name=body.name,
        rule_type=body.rule_type,
        config=body.config,
        enabled=body.enabled,
        run_order=body.run_order,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=FilterRuleResponse)
async def update_filter_rule(
    rule_id: int,
    body: FilterRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """更新一条过滤规则。"""
    rule = await db.get(FilterRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.name = body.name
    rule.rule_type = body.rule_type
    rule.config = body.config
    rule.enabled = body.enabled
    rule.run_order = body.run_order
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_filter_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """删除一条过滤规则。"""
    rule = await db.get(FilterRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "deleted"}


@router.post("/trigger", response_model=FilterTriggerResponse)
async def trigger_filter_all():
    """手动触发全量过滤（所有 pending topics）。"""
    # 加载 DB 中的规则配置到 registry
    from app.database import async_session

    async with async_session() as session:
        result = await session.execute(select(FilterRule).where(FilterRule.enabled == True))
        rules = result.scalars().all()
        for rule in rules:
            filter_registry.set_config(rule.rule_type, rule.config)

    from app.filter.scheduler import filter_pending_topics

    stats = await filter_pending_topics()
    return FilterTriggerResponse(**stats)


@router.post("/trigger/{topic_id}", response_model=FilterTriggerResponse)
async def trigger_filter_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    """手动触发单条 topic 的过滤。"""
    topic = await db.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 加载 DB 规则配置
    from app.database import async_session as async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(select(FilterRule).where(FilterRule.enabled == True))
        rules = result.scalars().all()
        for rule in rules:
            filter_registry.set_config(rule.rule_type, rule.config)

    from app.filter.scheduler import filter_single_topic

    filter_result = await filter_single_topic(topic)

    # 更新 DB
    topic_db = await db.get(Topic, topic_id)
    if filter_result.passed:
        topic_db.status = TopicStatus.FILTERED
        topic_db.category = filter_result.category or topic_db.category
        topic_db.priority = filter_result.priority_score
        await db.commit()
        return FilterTriggerResponse(total=1, filtered=1, rejected=0)
    else:
        topic_db.status = TopicStatus.REJECTED
        await db.commit()
        return FilterTriggerResponse(total=1, filtered=0, rejected=1)
