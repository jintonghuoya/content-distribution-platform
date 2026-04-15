import asyncio
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Patch BEFORE any app module is imported ──────────────────────────
# Ensure the project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

TEST_DATABASE_URL = "sqlite+aiosqlite:///file::memory:?cache=shared&uri=true"

# Patch settings.database_url so app.database picks it up
from config.settings import settings
settings.database_url = TEST_DATABASE_URL

# Now import app.database AFTER patching settings
import app.database as db_module

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Replace the engine and session in app.database so get_db uses test DB
db_module.engine = test_engine
db_module.async_session = TestingSession


async def override_get_db():
    async with TestingSession() as session:
        yield session


# Now it's safe to import app.main
from app.main import app
from app.database import Base, get_db


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Auto-discover registries (normally done in app lifespan, which doesn't
    # fire with ASGITransport in tests)
    from app.collector.registry import registry as collector_registry
    collector_registry.load_config()
    collector_registry.auto_discover()

    from app.filter.registry import registry as filter_registry
    filter_registry.auto_discover()

    from app.generator.registry import registry as generator_registry
    generator_registry.auto_discover()

    from app.distributor.registry import registry as distributor_registry
    distributor_registry.auto_discover()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db():
    async with TestingSession() as session:
        yield session


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
