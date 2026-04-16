"""小红书笔记生成器。

生成适合小红书平台的内容：
- 标题：20字以内，有吸引力
- 正文：300-800字，分段清晰，有emoji
- 标签：5个以内话题标签
"""

from app.generator.base import BaseGenerator, GenerationResult
from app.generator.registry import registry
from app.llm import llm_complete
from app.models.topic import Topic

SYSTEM_PROMPT = """你是一位小红书爆款内容创作者。根据热点话题撰写小红书笔记。

要求：
1. 标题：20字以内，有吸引力，可以用"！"增加情绪感
2. 正文：300-800字
3. 分段清晰，每段不超过3行
4. 适当使用 emoji 增加可读性
5. 语气亲切、口语化，像在跟朋友聊天
6. 结尾可以抛互动问题
7. 最后附上5个以内的标签，格式：#标签1# #标签2# #标签3#

输出格式：
标题行
空一行
正文内容
空一行
标签行"""

XHS_TEMPLATE = """请根据以下热点话题撰写一条小红书笔记：

话题：{title}
来源：{source}
热度：{heat}
分类：{category}

注意：
- 小红书用户喜欢"干货分享"和"真实体验"风格
- 避免过于书面化的表达
- 可以适当表达个人观点
- 标签要与话题相关，方便被搜索到"""


class XiaohongshuGenerator(BaseGenerator):
    name = "小红书笔记生成器"
    content_type = "xiaohongshu_note"

    async def generate(self, topic: Topic) -> GenerationResult:
        prompt = XHS_TEMPLATE.format(
            title=topic.title,
            source=topic.source,
            heat=topic.heat_value or "未知",
            category=topic.category or "未分类",
        )

        body = await llm_complete(prompt=prompt, system=SYSTEM_PROMPT, temperature=0.9)

        # 解析输出：第一行标题，最后一行标签
        lines = body.strip().split("\n")
        lines = [l for l in lines if l.strip()]  # 去空行

        title = lines[0].strip().lstrip("#").strip() if lines else topic.title
        # 限制标题20字
        title = title[:20]

        # 提取标签（最后一行如果全是 #xxx# 格式）
        tags = []
        body_lines = lines[1:] if len(lines) > 1 else lines
        if body_lines:
            last_line = body_lines[-1].strip()
            import re

            found_tags = re.findall(r"#([^#]+)#", last_line)
            if found_tags and len(found_tags) >= 2:
                tags = found_tags[:5]
                body_lines = body_lines[:-1]  # 去掉标签行

        body_text = "\n".join(body_lines).strip()

        return GenerationResult(
            content_type="xiaohongshu_note",
            title=title,
            body=body_text,
            metadata={
                "source_topic_id": topic.id,
                "source": topic.source,
                "tags": tags,
                "platform": "xiaohongshu",
            },
        )


registry.register(XiaohongshuGenerator())
