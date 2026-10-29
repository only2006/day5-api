from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import APIConnectionError, APIStatusError, APITimeoutError

import llm
from schemas import ChatRequest, ChatResponse, Usage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Chat API",
    version="0.1.0",
    description="Day 5 练习：把 CLI 机器人包成 HTTP 服务",
)

# 允许前端跨域调用（Day 6 会用到）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model": llm.MODEL}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """一次性返回完整回答。"""
    logger.info("收到 /chat 请求，消息数=%d", len(req.messages))

    try:
        content, usage = await llm.complete(
            req.messages, req.temperature, req.max_tokens
        )
    except APITimeoutError as exc:
        logger.error("模型请求超时")
        raise HTTPException(status_code=504, detail="模型响应超时") from exc
    except APIConnectionError as exc:
        logger.error("连接模型服务失败")
        raise HTTPException(status_code=502, detail="无法连接模型服务") from exc
    except APIStatusError as exc:
        logger.error("模型服务返回错误：%s", exc.status_code)
        raise HTTPException(
            status_code=502, detail=f"模型服务错误：{exc.status_code}"
        ) from exc

    return ChatResponse(
        content=content,
        model=llm.MODEL,
        usage=Usage(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )
        if usage
        else None,
    )


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """流式返回，SSE 格式。"""
    logger.info("收到 /chat/stream 请求，消息数=%d", len(req.messages))

    async def event_generator():
        try:
            async for piece in llm.stream(
                req.messages, req.temperature, req.max_tokens
            ):
                payload = json.dumps({"delta": piece}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:                      # noqa: BLE001
            logger.exception("流式生成失败")
            error = json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"data: {error}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",   # 关掉 Nginx 缓冲，否则不流式
        },
    )

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    """根路径直接返回前端页面。"""
    return FileResponse("static/index.html")