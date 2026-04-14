import asyncio

from celery import Celery
from celery.schedules import crontab
from loguru import logger

from config.settings import settings

app = Celery("cdp_revenue")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Asia/Shanghai"


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="collect_revenue")
def collect_revenue_task():
    """定时采集所有已分发内容的收益数据。"""
    from app.revenue.scheduler import collect_revenue_all

    logger.info("Starting scheduled revenue collection")
    results = _run_async(collect_revenue_all())
    logger.info(f"Revenue collection complete: {results}")
    return results


app.conf.beat_schedule = {
    "collect-revenue-every-hour": {
        "task": "collect_revenue",
        "schedule": crontab(minute=0),
    },
}
