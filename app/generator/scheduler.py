from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.generator.base import BaseGenerator, GenerationResult
from app.generator.registry import registry
from app.models.generated_content import GeneratedContent
from app.models.topic import Topic, TopicStatus
from config.settings import settings


async def generate_single(
    topic: Topic,
    generator: BaseGenerator,
) -> GeneratedContent | None:
    """用指定生成器为一条 topic 生成内容，存入 DB。

    Returns:
        生成的 GeneratedContent 对象，失败返回 None。
    """
    try:
        result = await generator.generate(topic)
    except Exception as e:
        logger.error(f"Generator {generator.content_type} failed on topic {topic.id}: {e}")
        return None

    content = GeneratedContent(
        topic_id=topic.id,
        content_type=result.content_type,
        title=result.title,
        body=result.body,
        prompt_name=generator.name,
        llm_model=settings.llm_model,
        status="draft",
        metadata_=result.metadata,
    )
    return content


async def generate_for_topic(
    topic_id: int,
    generator_name: str | None = None,
) -> list[GeneratedContent]:
    """为单条 topic 生成内容（指定生成器或全部生成器）。

    Returns:
        生成的 GeneratedContent 列表。
    """
    generators: list[BaseGenerator] = []
    if generator_name:
        gen = registry.get(generator_name)
        if gen:
            generators = [gen]
        else:
            logger.warning(f"Generator not found: {generator_name}")
            return []
    else:
        generators = registry.get_all()

    if not generators:
        logger.warning("No generators available")
        return []

    async with async_session() as session:
        topic = await session.get(Topic, topic_id)
        if not topic:
            logger.warning(f"Topic not found: {topic_id}")
            return []

        contents = []
        for gen in generators:
            content = await generate_single(topic, gen)
            if content:
                session.add(content)
                contents.append(content)

        if contents:
            topic.status = TopicStatus.PUBLISHED
            await session.commit()
            # Refresh to get IDs
            for c in contents:
                await session.refresh(c)

        logger.info(f"Generated {len(contents)} contents for topic {topic_id}")
        return contents


async def generate_for_filtered(batch_size: int | None = None) -> dict:
    """批量为 status=filtered 的 topic 生成内容。

    Returns:
        {"total": N, "generated": N}
    """
    if batch_size is None:
        batch_size = settings.generator_batch_size

    # 批量只生成社交媒体短文（微博帖子），不生成长文章
    gen = registry.get("social_post")
    generators = [gen] if gen else registry.get_all()
    if not generators:
        logger.warning("No generators available")
        return {"total": 0, "generated": 0}

    async with async_session() as session:
        stmt = (
            select(Topic)
            .where(Topic.status == TopicStatus.FILTERED)
            .order_by(Topic.priority.desc().nullslast())
            .limit(batch_size)
        )
        result = await session.execute(stmt)
        topics = list(result.scalars().all())

    if not topics:
        logger.info("No filtered topics to generate")
        return {"total": 0, "generated": 0}

    generated_count = 0

    async with async_session() as session:
        for topic in topics:
            # 重新加载到当前 session
            db_topic = await session.get(Topic, topic.id)
            if not db_topic:
                continue

            db_topic.status = TopicStatus.GENERATING

            topic_generated = 0
            for gen in generators:
                content = await generate_single(db_topic, gen)
                if content:
                    session.add(content)
                    generated_count += 1
                    topic_generated += 1

            # 只有成功生成了内容才改为 PUBLISHED
            if topic_generated > 0:
                db_topic.status = TopicStatus.PUBLISHED
            else:
                db_topic.status = TopicStatus.FILTERED  # 回退，下次可以重试

        await session.commit()

    logger.info(f"Generated {generated_count} contents from {len(topics)} topics")
    return {"total": len(topics), "generated": generated_count}
