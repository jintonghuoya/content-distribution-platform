from loguru import logger

from app.collector.registry import registry


async def collect_from_source(source: str) -> int:
    """执行单个源的采集任务，返回新增条数。"""
    from app.database import async_session
    from app.models.topic import Topic

    collector = registry._collectors.get(source)
    if not collector:
        logger.warning(f"Collector not found: {source}")
        return 0

    cfg = registry.get_config(source)
    max_items = cfg.get("max_items", 50)

    try:
        topics_data = await collector.fetch(max_items=max_items)
    except Exception as e:
        logger.error(f"[{source}] Fetch failed: {e}")
        return 0

    new_count = 0
    async with async_session() as session:
        for item in topics_data:
            # 按 source_id 去重
            from sqlalchemy import select

            stmt = select(Topic).where(Topic.source_id == item.source_id)
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                continue

            topic = Topic(
                title=item.title,
                source=item.source,
                source_id=item.source_id,
                source_url=item.source_url,
                rank=item.rank,
                heat_value=item.heat_value,
                raw_data=item.raw_data,
            )
            session.add(topic)
            new_count += 1

        await session.commit()

    logger.info(f"[{source}] Collected {len(topics_data)} items, {new_count} new")
    return new_count


async def collect_all() -> dict[str, int]:
    """执行所有已启用源的采集任务。"""
    results = {}
    for collector in registry.get_enabled():
        count = await collect_from_source(collector.source)
        results[collector.source] = count
    return results
