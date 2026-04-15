from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.distributor.base import DistributeResult
from app.distributor.registry import registry
from app.models.distribution import DistributionRecord
from app.models.generated_content import GeneratedContent


async def distribute_single(
    content: GeneratedContent,
    platform: str | None = None,
) -> list[DistributionRecord]:
    """为一条生成内容执行分发（指定平台或全部平台）。

    Returns:
        分发记录列表。
    """
    distributors = []
    if platform:
        dist = registry.get(platform)
        if dist:
            distributors = [dist]
        else:
            logger.warning(f"Distributor not found: {platform}")
            return []
    else:
        distributors = registry.get_all()

    if not distributors:
        logger.warning("No distributors available")
        return []

    records = []
    for dist in distributors:
        try:
            result: DistributeResult = await dist.publish(content)
        except Exception as e:
            logger.error(f"Distributor {dist.platform} failed on content {content.id}: {e}")
            result = DistributeResult(
                platform=dist.platform,
                success=False,
                error_message=str(e),
            )

        record = DistributionRecord(
            content_id=content.id,
            platform=result.platform,
            success=result.success,
            platform_content_id=result.platform_content_id,
            platform_url=result.platform_url,
            error_message=result.error_message,
        )
        records.append(record)

    return records


async def distribute_published(batch_size: int = 50) -> dict:
    """批量分发 status=draft 的生成内容。

    Returns:
        {"total": N, "distributed": N, "failed": N}
    """
    async with async_session() as session:
        stmt = (
            select(GeneratedContent)
            .where(GeneratedContent.status == "draft")
            .order_by(GeneratedContent.created_at.desc())
            .limit(batch_size)
        )
        result = await session.execute(stmt)
        contents = list(result.scalars().all())

    if not contents:
        logger.info("No draft content to distribute")
        return {"total": 0, "distributed": 0, "failed": 0}

    distributed = 0
    failed = 0

    async with async_session() as session:
        import random

        for i, content in enumerate(contents):
            db_content = await session.get(GeneratedContent, content.id)
            if not db_content:
                continue

            # 每条之间随机延迟 30~120 秒，避免触发平台风控
            if i > 0:
                import asyncio
                delay = random.uniform(30, 120)
                logger.info(f"Cooling down {delay:.0f}s before next distribution...")
                await asyncio.sleep(delay)

            records = await distribute_single(db_content)
            for record in records:
                session.add(record)
                if record.success:
                    distributed += 1
                else:
                    failed += 1

            if any(r.success for r in records):
                db_content.status = "published"

        await session.commit()

    logger.info(f"Distributed {len(contents)} contents: {distributed} success, {failed} failed")
    return {"total": len(contents), "distributed": distributed, "failed": failed}
