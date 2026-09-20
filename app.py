import hashlib
import hmac
import os
import time
import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

MAX_BODY_BYTES = 1_048_576
MAX_ECHO_CHARS = 4_000
MAX_MODEL_LEN = 256


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _api_key() -> str:
    return os.getenv("MOCK_LLM_API_KEY", "").strip()


DOCS_ENABLED = _env_flag("MOCK_LLM_DOCS", default=False)

app = FastAPI(
    title="mock-llm",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)


class ChatMessage(BaseModel):
    role: str = Field(min_length=1, max_length=64)
    content: str | list[Any] | dict[str, Any] | None = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(min_length=1, max_length=MAX_MODEL_LEN)
    messages: list[ChatMessage] = Field(min_length=1)
    temperature: float | None = None
    stream: bool | None = False


def _token_digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    expected = _api_key()
    if not expected:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    offered = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(_token_digest(offered), _token_digest(expected)):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_text(content: str | list[Any] | dict[str, Any] | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        text = content.get("text")
        return text if isinstance(text, str) else ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            text = item.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
    return "\n".join(parts)


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Request body too large"},
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length"},
            )
    return await call_next(request)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models", dependencies=[Depends(require_api_key)])
async def list_models() -> dict[str, Any]:
    return {
        "object": "list",
        "data": [
            {
                "id": "mock-llm",
                "object": "model",
                "created": 0,
                "owned_by": "mock-llm",
            }
        ],
    }


@app.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
async def chat_completions(request: ChatCompletionRequest) -> dict[str, Any]:
    if request.stream:
        raise HTTPException(status_code=400, detail="Streaming is not supported")

    prompt = extract_text(request.messages[-1].content).strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Last message has no text content")

    echo = prompt if len(prompt) <= MAX_ECHO_CHARS else prompt[:MAX_ECHO_CHARS] + "…"
    reply = f"[{request.model}] Mock response to: {echo}"
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(reply)

    return {
        "id": f"chatcmpl-mock-{uuid.uuid4().hex[:24]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
