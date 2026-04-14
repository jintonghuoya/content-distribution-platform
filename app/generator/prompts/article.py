from app.generator.base import BaseGenerator, GenerationResult
from app.generator.registry import registry
from app.llm import llm_complete
from app.models.topic import Topic

SYSTEM_PROMPT = """你是一位专业的内容创作者。根据热点话题撰写一篇结构完整、有深度的文章。

要求：
1. 标题吸引人但不标题党
2. 正文 800-1500 字
3. 结构清晰：引入背景 → 分析要点 → 总结展望
4. 语言通俗易懂，适合大众阅读
5. 客观中立，有理有据

请直接输出文章，包含标题和正文。"""


class ArticleGenerator(BaseGenerator):
    name = "文章生成器"
    content_type = "article"

    async def generate(self, topic: Topic) -> GenerationResult:
        prompt = f"""请根据以下热点话题撰写一篇文章：

标题：{topic.title}
来源：{topic.source}
热度：{topic.heat_value or '未知'}
分类：{topic.category or '未分类'}

请撰写一篇完整的文章。"""

        body = await llm_complete(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.8)

        # 提取标题（取第一行）
        lines = body.strip().split("\n")
        title = lines[0].strip().lstrip("#").strip() if lines else topic.title
        body_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else body

        return GenerationResult(
            content_type="article",
            title=title,
            body=body_text,
            metadata={"source_topic_id": topic.id, "source": topic.source},
        )


registry.register(ArticleGenerator())
