"""Unified Celery app — imports all task modules and defines a single beat schedule."""

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

# Initialize registries
registry.load_config()
registry.auto_discover()


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Collector tasks ──


@app.task(name="collect_all")
def collect_all_task():
    from app.collector.scheduler import collect_all

    logger.info("Beat: collect all sources")
    results = _run_async(collect_all())
    logger.info(f"Collection complete: {results}")
    return results


@app.task(name="collect_source")
def collect_source_task(source: str):
    from app.collector.scheduler import collect_from_source

    logger.info(f"Beat: collect {source}")
    count = _run_async(collect_from_source(source))
    return {"source": source, "new_count": count}


# ── Filter tasks ──


@app.task(name="filter_pending")
def filter_pending_task():
    from app.filter.scheduler import filter_pending_topics

    logger.info("Beat: filter pending topics")
    results = _run_async(filter_pending_topics())
    logger.info(f"Filter complete: {results}")
    return results


# ── Generator tasks ──


@app.task(name="generate_filtered")
def generate_filtered_task():
    from app.generator.scheduler import generate_for_filtered

    logger.info("Beat: generate for filtered topics")
    results = _run_async(generate_for_filtered())
    logger.info(f"Generation complete: {results}")
    return results


# ── Distributor tasks ──


@app.task(name="distribute_published")
def distribute_published_task():
    from app.distributor.registry import registry as distributor_registry
    from app.distributor.scheduler import distribute_published

    distributor_registry.auto_discover()
    logger.info("Beat: distribute published content")
    results = _run_async(distribute_published())
    logger.info(f"Distribution complete: {results}")
    return results


# ── Revenue tasks ──


@app.task(name="collect_revenue")
def collect_revenue_task():
    from app.revenue.scheduler import collect_revenue_all

    logger.info("Beat: collect revenue data")
    results = _run_async(collect_revenue_all())
    logger.info(f"Revenue collection complete: {results}")
    return results


# ── Beat schedule ──

beat_schedule = {
    # Collect all sources every 10 minutes
    "collect-all": {
        "task": "collect_all",
        "schedule": crontab(minute="*/10"),
    },
    # Filter pending topics every 10 minutes (offset by 2 min)
    "filter-pending": {
        "task": "filter_pending",
        "schedule": crontab(minute="2-59/10"),
    },
    # Generate content every 30 minutes
    "generate-filtered": {
        "task": "generate_filtered",
        "schedule": crontab(minute="5-59/30"),
    },
    # Distribute draft content every 10 minutes (offset by 7 min)
    "distribute-published": {
        "task": "distribute_published",
        "schedule": crontab(minute="7-59/10"),
    },
    # Collect revenue data every hour
    "collect-revenue": {
        "task": "collect_revenue",
        "schedule": crontab(minute=15),
    },
}

# Add per-source schedules
for collector in registry.get_enabled():
    cfg = registry.get_config(collector.source)
    interval = cfg.get("interval_seconds", 600)
    minutes = max(1, interval // 60)
    beat_schedule[f"collect-{collector.source}"] = {
        "task": "collect_source",
        "schedule": crontab(minute=f"*/{minutes}"),
        "args": (collector.source,),
    }

app.conf.beat_schedule = beat_schedule
