"""Integration tests for CDP API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Topics ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_topics_empty(client):
    resp = await client.get("/api/v1/topics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_topics_with_filters(client):
    resp = await client.get("/api/v1/topics", params={"source": "weibo", "status": "pending", "page": 1, "size": 10})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_topic_status_filter_with_data(client, db):
    """Insert topics with different statuses, filter by each status."""
    from app.models.topic import Topic, TopicStatus

    for status in [TopicStatus.PENDING, TopicStatus.FILTERED, TopicStatus.REJECTED]:
        t = Topic(title=f"test-{status.value}", source="test", source_id=f"src-{status.value}", status=status.value)
        db.add(t)
    await db.commit()

    for st in ["pending", "filtered", "rejected"]:
        resp = await client.get("/api/v1/topics", params={"status": st})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == st


@pytest.mark.asyncio
async def test_get_topic_not_found(client):
    resp = await client.get("/api/v1/topics/99999")
    assert resp.status_code == 404


# ── Filters ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_filter_rules(client):
    resp = await client.get("/api/v1/filters/rules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_filter_rule(client):
    rule = {
        "name": "test_keyword_block",
        "rule_type": "keyword_blacklist",
        "config": {"keywords": ["测试关键词"]},
        "enabled": True,
        "run_order": 100,
    }
    resp = await client.post("/api/v1/filters/rules", json=rule)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test_keyword_block"
    assert data["rule_type"] == "keyword_blacklist"
    assert data["config"]["keywords"] == ["测试关键词"]
    rule_id = data["id"]

    # Update
    rule["name"] = "test_keyword_block_updated"
    resp = await client.put(f"/api/v1/filters/rules/{rule_id}", json=rule)
    assert resp.status_code == 200
    assert resp.json()["name"] == "test_keyword_block_updated"

    # Delete
    resp = await client.delete(f"/api/v1/filters/rules/{rule_id}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_create_heat_threshold_rule(client):
    rule = {
        "name": "test_heat",
        "rule_type": "heat_threshold",
        "config": {"min_heat": 100, "max_heat": 50000},
        "enabled": True,
        "run_order": 1,
    }
    resp = await client.post("/api/v1/filters/rules", json=rule)
    assert resp.status_code == 200
    assert resp.json()["config"]["min_heat"] == 100
    # Cleanup
    await client.delete(f"/api/v1/filters/rules/{resp.json()['id']}")


# ── Generators ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_generators(client):
    resp = await client.get("/api/v1/generators/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_trigger_generate_all_async(client):
    """批量生成应该异步返回，不超时。"""
    with patch("app.workers.generator_worker.generate_filtered_task") as mock_task:
        mock_task.delay = AsyncMock()
        resp = await client.post("/api/v1/generators/trigger")
        assert resp.status_code == 200
        data = resp.json()
        assert "任务已提交" in data["message"]
        mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_generate_topic_not_found(client):
    resp = await client.post("/api/v1/generators/trigger/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_generated_content_empty(client):
    resp = await client.get("/api/v1/generators/content")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


# ── Distributors ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_distributors(client):
    resp = await client.get("/api/v1/distributors/")
    assert resp.status_code == 200
    distributors = resp.json()
    assert isinstance(distributors, list)
    names = [d["platform"] for d in distributors]
    assert "weibo" in names


@pytest.mark.asyncio
async def test_distribute_content_not_found(client):
    resp = await client.post("/api/v1/distributors/trigger/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_distribution_records(client):
    resp = await client.get("/api/v1/distributors/records")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Sources ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_sources(client):
    resp = await client.get("/api/v1/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert isinstance(sources, list)


# ── Settings / Platforms ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_platforms(client):
    resp = await client.get("/api/v1/settings/platforms")
    assert resp.status_code == 200
    platforms = resp.json()
    assert isinstance(platforms, list)
    names = [p["name"] for p in platforms]
    assert "weibo" in names
    assert "wechat" in names


@pytest.mark.asyncio
async def test_upsert_platform(client):
    resp = await client.put("/api/v1/settings/platforms/weibo", json={
        "display_name": "微博",
        "cookie": "test_cookie_value",
        "api_key": "",
        "app_secret": "",
        "app_id": "",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "weibo"
    assert data["cookie"] == "test_cookie_value"


# ── Revenue ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_revenue_records(client):
    resp = await client.get("/api/v1/revenue/records")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_revenue_summary(client):
    resp = await client.get("/api/v1/revenue/summary")
    assert resp.status_code == 200


# ── Schema validation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generated_content_response_coerces_metadata(db):
    """GeneratedContentResponse should handle SQLAlchemy MetaData without error."""
    from app.schemas.generator import GeneratedContentResponse
    from sqlalchemy import MetaData as SA_MetaData

    # Simulate SQLAlchemy returning its MetaData object instead of dict/None
    obj = type("FakeObj", (), {
        "id": 1, "topic_id": 1, "content_type": "article",
        "title": "test", "body": "test body", "prompt_name": "test",
        "llm_model": "test", "status": "draft",
        "metadata": SA_MetaData(),  # This is what SQLAlchemy returns
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })()

    result = GeneratedContentResponse.model_validate(obj)
    assert result.metadata is None  # Should coerce to None
