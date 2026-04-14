import asyncio

from celery import Celery
from loguru import logger

from config.settings import settings

app = Celery("cdp_distributor")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Asia/Shanghai"


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="distribute_published")
def distribute_published_task():
    """定时分发已生成的 draft 内容。"""
    from app.distributor.registry import registry
    from app.distributor.scheduler import distribute_published

    registry.auto_discover()
    logger.info("Starting scheduled distribution")
    results = _run_async(distribute_published())
    logger.info(f"Distribution complete: {results}")
    return results


@app.task(name="distribute_content")
def distribute_content_task(content_id: int, platform: str | None = None):
    """分发单条内容。"""
    from app.database import async_session
    from app.distributor.registry import registry
    from app.distributor.scheduler import distribute_single
    from app.models.generated_content import GeneratedContent

    registry.auto_discover()

    async def _run():
        async with async_session() as session:
            content = await session.get(GeneratedContent, content_id)
            if not content:
                return {"error": "Content not found"}
            records = await distribute_single(content, platform)
            for record in records:
                session.add(record)
            await session.commit()
            return {"content_id": content_id, "distributed": len(records)}

    return _run_async(_run())
