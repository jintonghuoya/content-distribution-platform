from app.generator.base import BaseGenerator, GenerationResult
from app.generator.registry import registry
from app.llm import llm_complete
from app.models.topic import Topic

SYSTEM_PROMPT = """你是一位社交媒体内容运营专家。根据热点话题撰写适合微博/微信发布的短文。

要求：
1. 正文 100-300 字
2. 风格活泼，有吸引力
3. 可以适当使用 emoji 增加表现力
4. 包含话题标签（#话题#）
5. 结尾可以抛出互动问题引发讨论

请直接输出正文内容。"""


class SocialPostGenerator(BaseGenerator):
    name = "社交媒体文案生成器"
    content_type = "social_post"

    async def generate(self, topic: Topic) -> GenerationResult:
        prompt = f"""请根据以下热点话题撰写一条社交媒体短文：

话题：{topic.title}
来源：{topic.source}
热度：{topic.heat_value or '未知'}
分类：{topic.category or '未分类'}

请撰写一条适合社交媒体发布的短文。"""

        body = await llm_complete(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.9)

        return GenerationResult(
            content_type="social_post",
            title=topic.title,
            body=body.strip(),
            metadata={"source_topic_id": topic.id, "source": topic.source},
        )


registry.register(SocialPostGenerator())
