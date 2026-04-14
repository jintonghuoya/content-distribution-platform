import json

from loguru import logger

from app.filter.base import FilterResult
from app.llm import llm_complete
from app.models.topic import Topic

SYSTEM_PROMPT = """你是一个热点话题内容评估专家。你需要评估每条热点话题是否适合生成内容。

评估维度：
1. 内容质量：标题是否有实质性内容，而非纯广告或无意义内容
2. 受众相关性：话题是否能引起广泛兴趣
3. 内容生成潜力：是否能基于此话题写出有价值的文章

对每条话题，返回一个 JSON 对象：
{
  "passed": true/false,
  "category": "科技/娱乐/社会/体育/财经/其他",
  "priority_score": 0.0-10.0,
  "reason": "简短评估原因"
}

请对每条话题逐一评估，返回 JSON 数组。"""

USER_PROMPT_TEMPLATE = """请评估以下热点话题：

{topics_json}

请返回 JSON 数组，每个元素对应一条话题的评估结果。"""


def _build_topics_json(topics: list[Topic]) -> str:
    items = []
    for t in topics:
        items.append({
            "id": t.id,
            "title": t.title,
            "source": t.source,
            "heat_value": t.heat_value,
            "category": t.category,
        })
    return json.dumps(items, ensure_ascii=False, indent=2)


async def evaluate_with_llm(topics: list[Topic]) -> list[FilterResult]:
    """用 LLM 批量评估 topics，返回 FilterResult 列表。

    如果 LLM 调用失败，返回全部通过（fail-open）。
    """
    if not topics:
        return []

    topics_json = _build_topics_json(topics)
    prompt = USER_PROMPT_TEMPLATE.format(topics_json=topics_json)

    try:
        text = await llm_complete(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.3)

        # 尝试从响应中提取 JSON 数组
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        results_data = json.loads(text)
        if not isinstance(results_data, list):
            results_data = [results_data]

        results = []
        for item in results_data:
            results.append(FilterResult(
                passed=item.get("passed", True),
                category=item.get("category"),
                priority_score=float(item.get("priority_score", 5.0)),
                reason=item.get("reason", ""),
            ))

        # 补齐不足的结果（fail-open）
        while len(results) < len(topics):
            results.append(FilterResult(passed=True, priority_score=5.0, reason="LLM 未返回结果"))

        logger.info(f"LLM evaluated {len(topics)} topics: {sum(1 for r in results if r.passed)} passed")
        return results

    except Exception as e:
        logger.error(f"LLM evaluation failed: {e}")
        return [FilterResult(passed=True, priority_score=5.0, reason=f"LLM 调用失败: {e}") for _ in topics]
