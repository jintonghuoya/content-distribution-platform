import asyncio

from celery import Celery
from loguru import logger

from config.settings import settings

app = Celery("cdp_filter")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Asia/Shanghai"


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="filter_pending")
def filter_pending_task():
    """定时过滤所有 pending topics。"""
    from app.filter.scheduler import filter_pending_topics

    logger.info("Starting scheduled filter for pending topics")
    results = _run_async(filter_pending_topics())
    logger.info(f"Filter complete: {results}")
    return results


@app.task(name="filter_topic")
def filter_topic_task(topic_id: int):
    """过滤单条 topic。"""
    from app.filter.scheduler import filter_single_topic

    logger.info(f"Filtering topic {topic_id}")
    # 需要重新加载 topic
    from app.database import async_session
    from app.models.topic import Topic

    async def _run():
        async with async_session() as session:
            topic = await session.get(Topic, topic_id)
            if not topic:
                return {"error": "Topic not found"}
            result = await filter_single_topic(topic)
            return {"passed": result.passed, "reason": result.reason}

    return _run_async(_run())
