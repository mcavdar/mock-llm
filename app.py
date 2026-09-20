from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[dict]
    temperature: float | None = None


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    user_message = request.messages[-1]["content"]

    return {
        "id": "mock-chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        f"[{request.model}] "
                        f"Mock response to: {user_message}"
                    ),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20,
        },
    }
