"""Shared LLM utility — used by both filter and generator modules."""

from anthropic import AsyncAnthropic
from loguru import logger

from config.settings import settings


async def llm_complete(
    prompt: str,
    system: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """Call the LLM and return the text response.

    Args:
        prompt: The user message.
        system: System prompt.
        model: Model override (defaults to settings.llm_model).
        max_tokens: Max tokens in response.
        temperature: Sampling temperature.

    Returns:
        The text content of the response.
    """
    client = AsyncAnthropic(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url if settings.llm_base_url else None,
        timeout=120.0,
    )
    resp = await client.messages.create(
        model=model or settings.llm_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system or "You are a helpful content assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text
    logger.debug(f"LLM response ({len(text)} chars, model={model or settings.llm_model})")
    return text
