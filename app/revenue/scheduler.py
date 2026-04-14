from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.models.distribution import DistributionRecord
from app.models.revenue import RevenueRecord


async def collect_revenue_for_distribution(distribution: DistributionRecord) -> RevenueRecord | None:
    """为一条分发记录采集收益数据。

    目前返回占位数据，待各平台 tracker 实现后对接。
    """
    # TODO: 当平台 tracker 实现后，调用对应 tracker.fetch_metrics()
    record = RevenueRecord(
        distribution_id=distribution.id,
        platform=distribution.platform,
        content_id=distribution.content_id,
        views=0,
        likes=0,
        comments=0,
        shares=0,
        revenue_amount=0.0,
    )
    return record


async def collect_revenue_all(batch_size: int = 100) -> dict:
    """为所有成功的分发记录采集收益数据。

    Returns:
        {"total": N, "collected": N}
    """
    async with async_session() as session:
        # 查找已分发成功但尚未采集收益的记录
        stmt = (
            select(DistributionRecord)
            .where(DistributionRecord.success == True)
            .order_by(DistributionRecord.published_at.desc())
            .limit(batch_size)
        )
        result = await session.execute(stmt)
        distributions = list(result.scalars().all())

    if not distributions:
        logger.info("No distribution records to collect revenue for")
        return {"total": 0, "collected": 0}

    # 过滤掉已有收益记录的 distribution
    async with async_session() as session:
        existing_ids = set()
        for dist in distributions:
            rev_stmt = select(RevenueRecord).where(RevenueRecord.distribution_id == dist.id)
            rev_result = await session.execute(rev_stmt)
            if rev_result.scalar_one_or_none():
                existing_ids.add(dist.id)

    to_collect = [d for d in distributions if d.id not in existing_ids]
    collected = 0

    async with async_session() as session:
        for dist in to_collect:
            record = await collect_revenue_for_distribution(dist)
            if record:
                session.add(record)
                collected += 1

        await session.commit()

    logger.info(f"Collected revenue for {collected}/{len(distributions)} distributions")
    return {"total": len(distributions), "collected": collected}


async def get_revenue_summary(
    platform: str | None = None,
    days: int = 30,
) -> dict:
    """获取收益汇总数据。

    Returns:
        汇总统计 dict。
    """
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func as sa_func

    async with async_session() as session:
        query = select(RevenueRecord)
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.where(RevenueRecord.recorded_at >= since)

        if platform:
            query = query.where(RevenueRecord.platform == platform)

        result = await session.execute(query)
        records = list(result.scalars().all())

    if not records:
        return {
            "total_revenue": 0.0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "by_platform": {},
            "record_count": 0,
        }

    total_revenue = sum(r.revenue_amount for r in records)
    total_views = sum(r.views for r in records)
    total_likes = sum(r.likes for r in records)
    total_comments = sum(r.comments for r in records)
    total_shares = sum(r.shares for r in records)

    # 按平台汇总
    by_platform: dict = {}
    for r in records:
        if r.platform not in by_platform:
            by_platform[r.platform] = {
                "revenue": 0.0,
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
            }
        p = by_platform[r.platform]
        p["revenue"] += r.revenue_amount
        p["views"] += r.views
        p["likes"] += r.likes
        p["comments"] += r.comments
        p["shares"] += r.shares

    return {
        "total_revenue": total_revenue,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "by_platform": by_platform,
        "record_count": len(records),
    }
