from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.api.filters import router as filters_router
from app.api.generators import router as generators_router
from app.api.topics import router as topics_router
from app.collector.registry import registry
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}")

    # Collector registry
    registry.load_config()
    registry.auto_discover()
    enabled = registry.get_enabled()
    logger.info(f"Enabled collectors: {[c.name for c in enabled]}")

    # Filter registry
    from app.filter.registry import registry as filter_registry
    filter_registry.auto_discover()
    logger.info(f"Registered filters: {[f.name for f in filter_registry.get_all()]}")

    # Generator registry
    from app.generator.registry import registry as generator_registry
    generator_registry.auto_discover()
    logger.info(f"Registered generators: {[g.name for g in generator_registry.get_all()]}")

    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    description="热点话题感知-过滤-内容生成-分发平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(topics_router)
app.include_router(filters_router)
app.include_router(generators_router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/v1/sources")
async def list_sources():
    """列出所有采集源及其状态。"""
    sources_cfg = registry._config.get("sources", {})
    return [
        {
            "source": source,
            "name": collector.name,
            "enabled": sources_cfg.get(source, {}).get("enabled", False),
            "interval_seconds": sources_cfg.get(source, {}).get("interval_seconds", 0),
        }
        for source, collector in registry._collectors.items()
    ]


def main():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)


if __name__ == "__main__":
    main()
