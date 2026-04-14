import asyncio

from celery import Celery
from celery.schedules import crontab
from loguru import logger

from app.collector.registry import registry
from config.settings import settings

app = Celery("cdp")
app.conf.broker_url = settings.celery_broker_url
app.conf.result_backend = settings.celery_result_backend
app.conf.timezone = "Asia/Shanghai"

# 初始化采集器注册
registry.load_config()
registry.auto_discover()


def _run_async(coro):
    """在 Celery 同步 worker 中运行异步协程的辅助函数。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(name="collect_all")
def collect_all_task():
    """定时采集所有已启用源。"""
    from app.collector.scheduler import collect_all

    logger.info("Starting scheduled collection of all sources")
    results = _run_async(collect_all())
    logger.info(f"Collection complete: {results}")
    return results


@app.task(name="collect_source")
def collect_source_task(source: str):
    """采集单个源。"""
    from app.collector.scheduler import collect_from_source

    logger.info(f"Starting collection for source: {source}")
    count = _run_async(collect_from_source(source))
    logger.info(f"[{source}] Collected {count} new items")
    return {"source": source, "new_count": count}


# 为每个已启用的源生成定时任务
def _build_beat_schedule() -> dict:
    schedule = {
        "collect-all-every-10min": {
            "task": "collect_all",
            "schedule": crontab(minute="*/10"),
        },
    }
    for collector in registry.get_enabled():
        cfg = registry.get_config(collector.source)
        interval = cfg.get("interval_seconds", 600)
        minutes = max(1, interval // 60)
        schedule[f"collect-{collector.source}"] = {
            "task": "collect_source",
            "schedule": crontab(minute=f"*/{minutes}"),
            "args": (collector.source,),
        }
    return schedule


app.conf.beat_schedule = _build_beat_schedule()
