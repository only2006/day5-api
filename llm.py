import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from openai import AsyncOpenAI

from schemas import Message

load_dotenv()

MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")

# 注意：这里是 AsyncOpenAI，不是 OpenAI
client = AsyncOpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=BASE_URL,
)


def _to_dicts(messages: list[Message]) -> list[dict]:
    return [m.model_dump() for m in messages]


async def complete(
    messages: list[Message],
    temperature: float,
    max_tokens: int,
) -> tuple[str, object]:
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=_to_dicts(messages),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or "", resp.usage


async def stream(
    messages: list[Message],
    temperature: float,
    max_tokens: int,
) -> AsyncIterator[str]:
    result = await client.chat.completions.create(
        model=MODEL,
        messages=_to_dicts(messages),
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
        stream_options={"include_usage": True},
    )
    async for chunk in result:
        if chunk.choices:
            piece = chunk.choices[0].delta.content
            if piece:
                yield piece