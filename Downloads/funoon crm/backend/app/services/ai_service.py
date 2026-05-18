import anthropic
import structlog

from app.config import settings

logger = structlog.get_logger()

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS_DEFAULT = 1024

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def complete(
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int = MAX_TOKENS_DEFAULT,
) -> anthropic.types.Message:
    kwargs: dict = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools

    try:
        response = await client.messages.create(**kwargs)
        logger.info(
            "claude_call",
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return response
    except Exception as e:
        logger.error("claude_call_failed", error=str(e))
        raise
