import asyncio
import os
import random
from datetime import datetime, timezone, timedelta

from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.distributor.base import DistributeResult
from app.distributor.registry import registry
from app.models.distribution import DistributionRecord
from app.models.generated_content import GeneratedContent


async def _has_successful_distribution(content_id: int, platform: str) -> bool:
    """检查指定内容是否已在指定平台成功分发。"""
    async with async_session() as session:
        stmt = (
            select(DistributionRecord)
            .where(
                DistributionRecord.content_id == content_id,
                DistributionRecord.platform == platform,
                DistributionRecord.success.is_(True),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

# 批量自动分发禁止时间段（24h制）
QUIET_HOURS = (0, 7)  # 0:00 ~ 7:00 不发布

# 发布前随机延迟范围（秒）
RANDOM_DELAY_MIN = 120  # 2 分钟
RANDOM_DELAY_MAX = 300  # 5 分钟

# 时区：读取 TZ 环境变量，默认 Asia/Singapore (UTC+8)
_TZ_OFFSET = int(os.environ.get("TZ_OFFSET_HOURS", "8"))


def _now_local() -> datetime:
    """获取本地时区的当前时间。"""
    return datetime.now(timezone(timedelta(hours=_TZ_OFFSET)))


def _is_quiet_hour() -> bool:
    """当前时间是否在禁止发布的时间段内。"""
    hour = _now_local().hour
    return QUIET_HOURS[0] <= hour < QUIET_HOURS[1]


async def _random_delay(min_s: float = RANDOM_DELAY_MIN, max_s: float = RANDOM_DELAY_MAX) -> float:
    """随机等待，返回实际等待秒数。"""
    delay = random.uniform(min_s, max_s)
    logger.info(f"Random delay: {delay:.0f}s before publishing...")
    await asyncio.sleep(delay)
    return delay


async def distribute_single(
    content: GeneratedContent,
    platform: str | None = None,
) -> list[DistributionRecord]:
    """为一条生成内容执行分发（指定平台或全部平台）。

    手动触发，不检查时间窗口，但有随机延迟。
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

    # 手动分发直接发，不加延迟

    records = []
    for dist in distributors:
        if await _has_successful_distribution(content.id, dist.platform):
            logger.info(f"Content {content.id} already published to {dist.platform}, skipping")
            continue

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
            mode=result.mode,
            platform_content_id=result.platform_content_id,
            platform_url=result.platform_url,
            package_data=result.package_data,
            error_message=result.error_message,
        )
        records.append(record)

        # 多平台分发时，平台之间也直接发
        if len(distributors) > 1:
            pass

    return records


async def distribute_published(batch_size: int = 50) -> dict:
    """批量分发 status=draft 的生成内容。

    自动触发，会检查禁止时间段，每条之间有随机延迟。
    Returns:
        {"total": N, "distributed": N, "failed": N, "skipped_quiet_hour": N}
    """
    if _is_quiet_hour():
        logger.info(f"Skipping distribution: quiet hours {QUIET_HOURS[0]}:00-{QUIET_HOURS[1]}:00")
        return {"total": 0, "distributed": 0, "failed": 0, "skipped_quiet_hour": 1}

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
        return {"total": 0, "distributed": 0, "failed": 0, "skipped_quiet_hour": 0}

    distributed = 0
    failed = 0

    async with async_session() as session:
        for i, content in enumerate(contents):
            # 每条之前检查是否进入安静时段
            if _is_quiet_hour():
                logger.info(f"Entered quiet hours, stopping batch. Published {i}/{len(contents)}")
                break

            db_content = await session.get(GeneratedContent, content.id)
            if not db_content:
                continue

            # 跳过已成功分发的平台
            pending_dists = []
            for dist in registry.get_all():
                if await _has_successful_distribution(db_content.id, dist.platform):
                    logger.info(f"Content {db_content.id} already published to {dist.platform}, skipping")
                    continue
                pending_dists.append(dist)

            if not pending_dists:
                continue

            # 每条之间随机延迟 60~180 秒
            if i > 0:
                await _random_delay(60, 180)

            records = []
            for dist in pending_dists:
                try:
                    result: DistributeResult = await dist.publish(db_content)
                except Exception as e:
                    logger.error(f"Distributor {dist.platform} failed on content {db_content.id}: {e}")
                    result = DistributeResult(
                        platform=dist.platform,
                        success=False,
                        error_message=str(e),
                    )
                record = DistributionRecord(
                    content_id=db_content.id,
                    platform=result.platform,
                    success=result.success,
                    mode=result.mode,
                    platform_content_id=result.platform_content_id,
                    platform_url=result.platform_url,
                    package_data=result.package_data,
                    error_message=result.error_message,
                )
                session.add(record)
                records.append(record)
                if record.success:
                    distributed += 1
                else:
                    failed += 1

            if any(r.success for r in records):
                db_content.status = "published"

        await session.commit()

    logger.info(f"Distributed {len(contents)} contents: {distributed} success, {failed} failed")
    return {"total": len(contents), "distributed": distributed, "failed": failed, "skipped_quiet_hour": 0}
