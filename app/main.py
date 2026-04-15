from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from loguru import logger

from app.api.distributors import router as distributors_router
from app.api.filters import router as filters_router
from app.api.generators import router as generators_router
from app.api.revenue import router as revenue_router
from app.api.settings import router as settings_router
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

    # Distributor registry
    from app.distributor.registry import registry as distributor_registry
    distributor_registry.auto_discover()
    logger.info(f"Registered distributors: {[d.name for d in distributor_registry.get_all()]}")

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
app.include_router(distributors_router)
app.include_router(revenue_router)
app.include_router(settings_router)


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


@app.put("/api/v1/sources/{source_name}")
async def toggle_source(source_name: str, body: dict):
    """启用/禁用指定采集源。"""
    if source_name not in registry._collectors:
        raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")

    enabled = body.get("enabled")
    if enabled is None:
        raise HTTPException(status_code=400, detail="'enabled' field is required")

    # Update in-memory config
    if "sources" not in registry._config:
        registry._config["sources"] = {}
    if source_name not in registry._config["sources"]:
        registry._config["sources"][source_name] = {}
    registry._config["sources"][source_name]["enabled"] = enabled

    # Persist to sources.yaml
    sources_yaml_path = Path(__file__).resolve().parent.parent / "config" / "sources.yaml"
    if sources_yaml_path.exists():
        with open(sources_yaml_path, "r") as f:
            data = yaml.safe_load(f) or {}
        if "sources" in data and source_name in data["sources"]:
            data["sources"][source_name]["enabled"] = enabled
            with open(sources_yaml_path, "w") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    return {
        "source": source_name,
        "enabled": enabled,
        "message": f"Source '{source_name}' {'enabled' if enabled else 'disabled'}",
    }


def main():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)


if __name__ == "__main__":
    main()
