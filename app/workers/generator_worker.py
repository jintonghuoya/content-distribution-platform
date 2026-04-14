import asyncio

from celery import Celery
from loguru import logger

from config.settings import settings

app = Celery("cdp_generator")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Asia/Shanghai"


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="generate_filtered")
def generate_filtered_task():
    """定时为所有 filtered topics 生成内容。"""
    from app.generator.scheduler import generate_for_filtered

    logger.info("Starting scheduled generation for filtered topics")
    results = _run_async(generate_for_filtered())
    logger.info(f"Generation complete: {results}")
    return results


@app.task(name="generate_topic")
def generate_topic_task(topic_id: int, generator_name: str | None = None):
    """为单条 topic 生成内容。"""
    from app.generator.scheduler import generate_for_topic

    logger.info(f"Generating content for topic {topic_id}")
    contents = _run_async(generate_for_topic(topic_id, generator_name))
    return {"topic_id": topic_id, "generated": len(contents)}
