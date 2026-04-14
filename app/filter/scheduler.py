from loguru import logger
from sqlalchemy import select

from app.database import async_session
from app.filter.base import FilterResult
from app.filter.registry import registry
from app.models.topic import Topic, TopicStatus
from config.settings import settings


async def filter_single_topic(topic: Topic) -> FilterResult:
    """对单条 topic 执行完整过滤流程（规则 + LLM），返回最终结果。

    注意：此函数只返回结果，不修改数据库。调用方负责持久化。
    """
    # 阶段 1：规则过滤
    combined_score = 0.0
    category = topic.category

    for f in registry.get_enabled():
        config = registry.get_config(f.filter_type)
        try:
            result = await f.evaluate(topic, config)
        except Exception as e:
            logger.error(f"Filter {f.filter_type} failed on topic {topic.id}: {e}")
            continue

        if not result.passed:
            return result

        combined_score += result.priority_score
        if result.category:
            category = result.category

    # 阶段 2：LLM 过滤（如果启用且分数达到阈值）
    if settings.filter_llm_enabled and combined_score >= settings.filter_llm_threshold:
        from app.filter.llm import evaluate_with_llm

        llm_results = await evaluate_with_llm([topic])
        if llm_results:
            llm_result = llm_results[0]
            if not llm_result.passed:
                return llm_result
            combined_score += llm_result.priority_score
            if llm_result.category:
                category = llm_result.category

    return FilterResult(
        passed=True,
        category=category,
        priority_score=combined_score,
        reason="通过所有过滤规则",
    )


async def filter_pending_topics(batch_size: int | None = None) -> dict:
    """批量过滤所有 status=pending 的 topic。

    Returns:
        {"total": N, "filtered": N, "rejected": N}
    """
    if batch_size is None:
        batch_size = settings.filter_batch_size

    async with async_session() as session:
        stmt = (
            select(Topic)
            .where(Topic.status == TopicStatus.PENDING)
            .order_by(Topic.collected_at.desc())
            .limit(batch_size)
        )
        result = await session.execute(stmt)
        topics = list(result.scalars().all())

    if not topics:
        logger.info("No pending topics to filter")
        return {"total": 0, "filtered": 0, "rejected": 0}

    # 批量 LLM 评估（如果启用）
    llm_results_map: dict[int, FilterResult] = {}
    if settings.filter_llm_enabled:
        # 先做规则过滤，收集通过规则的 topics
        rule_passed = []
        for topic in topics:
            combined_score = 0.0
            rejected = False
            for f in registry.get_enabled():
                config = registry.get_config(f.filter_type)
                try:
                    result = await f.evaluate(topic, config)
                except Exception as e:
                    logger.error(f"Filter {f.filter_type} failed on topic {topic.id}: {e}")
                    continue
                if not result.passed:
                    rejected = True
                    break
                combined_score += result.priority_score
            if not rejected and combined_score >= settings.filter_llm_threshold:
                rule_passed.append(topic)

        if rule_passed:
            from app.filter.llm import evaluate_with_llm

            batch_results = await evaluate_with_llm(rule_passed)
            for topic, result in zip(rule_passed, batch_results):
                llm_results_map[topic.id] = result

    # 逐条处理
    filtered_count = 0
    rejected_count = 0

    async with async_session() as session:
        for topic in topics:
            # 重新加载到当前 session
            db_topic = await session.get(Topic, topic.id)
            if not db_topic:
                continue

            # 规则过滤
            combined_score = 0.0
            category = db_topic.category
            rejected_by_rule = False
            reject_reason = ""

            for f in registry.get_enabled():
                config = registry.get_config(f.filter_type)
                try:
                    result = await f.evaluate(db_topic, config)
                except Exception as e:
                    logger.error(f"Filter {f.filter_type} failed on topic {db_topic.id}: {e}")
                    continue

                if not result.passed:
                    rejected_by_rule = True
                    reject_reason = result.reason
                    break

                combined_score += result.priority_score
                if result.category:
                    category = result.category

            if rejected_by_rule:
                db_topic.status = TopicStatus.REJECTED
                rejected_count += 1
                logger.debug(f"Topic {db_topic.id} rejected by rule: {reject_reason}")
                continue

            # LLM 过滤
            if db_topic.id in llm_results_map:
                llm_result = llm_results_map[db_topic.id]
                if not llm_result.passed:
                    db_topic.status = TopicStatus.REJECTED
                    rejected_count += 1
                    logger.debug(f"Topic {db_topic.id} rejected by LLM: {llm_result.reason}")
                    continue
                combined_score += llm_result.priority_score
                if llm_result.category:
                    category = llm_result.category

            # 通过所有过滤
            db_topic.status = TopicStatus.FILTERED
            db_topic.category = category
            db_topic.priority = combined_score
            filtered_count += 1

        await session.commit()

    logger.info(f"Filtered {len(topics)} topics: {filtered_count} passed, {rejected_count} rejected")
    return {"total": len(topics), "filtered": filtered_count, "rejected": rejected_count}
